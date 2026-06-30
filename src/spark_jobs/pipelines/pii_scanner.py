"""
Spark job: Scan Iceberg tables for PII and update the metadata store.

For each table in the lakehouse:
    1. Load PII detection rules from the metadata store (pii_categories).
    2. For every unscanned column, run the PIIClassifier.
    3. Write classification results back to columns_metadata.

Usage::

    spark-submit pipelines/pii_scanner.py
"""

from __future__ import annotations

import json
import sys

from core.config import load_config
from core.connection import create_engine_from_config, create_session
from core.enums import DetectionMethod, PIICategory, SensitivityLevel
from core.spark_session import build_spark_session

from metadata_proccessor import CatalogClient, DataSampler
from metadata_store.model import PIICategoryModel
from metadata_store.repository import MetadataRepository

from pii_classification import PIIClassifier
from pii_classification.dtos import ClassificationResult, PIIRule


# ------------------------------------------------------------------ #
# Mapping helpers
# ------------------------------------------------------------------ #

# Map detection-method strings (from ClassificationResult) to the DB enum.
_DETECTION_METHOD_MAP: dict[DetectionMethod, str] = {
    DetectionMethod.REGEX: "REGEX",
    DetectionMethod.MANUAL: "MANUAL",
    DetectionMethod.HYBRID: "HYBRID",
    DetectionMethod.LLM: "LLM",
    DetectionMethod.UNKNOWN: "UNKNOWN",
}


def _build_pii_rules(
    repo: MetadataRepository,
) -> list[PIIRule]:
    """Load all PII categories from the DB and convert to PIIRule DTOs."""
    categories: list[PIICategoryModel] = repo.get_all_pii_categories()
    rules: list[PIIRule] = []

    for cat in categories:
        try:
            pii_enum = PIICategory(cat.code)
        except ValueError:
            print(f"[WARN] Unknown PII category code in DB: {cat.code!r}, skipping")
            continue

        sensitivity = SensitivityLevel.NONE
        if cat.default_sensitivity_level is not None:
            try:
                sensitivity = SensitivityLevel(cat.default_sensitivity_level.code)
            except ValueError:
                print(
                    f"[WARN] Unknown sensitivity level: "
                    f"{cat.default_sensitivity_level.code!r} "
                    f"for category {cat.code!r}, defaulting to NONE"
                )

        aliases = cat.column_name_aliases or []

        rules.append(
            PIIRule(
                pii_category=pii_enum,
                aliases=aliases,
                regex_pattern=cat.regex_pattern,
                default_sensitivity=sensitivity,
            )
        )

    return rules


def _apply_result(
    repo: MetadataRepository,
    column_id: int,
    result: ClassificationResult,
    sample_values: list,
) -> None:
    """Write a ClassificationResult back to the metadata store."""

    pii_category_id = None
    sensitivity_level_id = None

    if result.pii_category is not None:
        pii_row = repo.get_pii_category(result.pii_category.value)
        if pii_row is not None:
            pii_category_id = pii_row.id

    if result.sensitivity is not None:
        sens_row = repo.get_sensitivity_level(result.sensitivity.value)
        if sens_row is not None:
            sensitivity_level_id = sens_row.id

    # Map the enum to the DB detection_method value
    detection_method = result.detection_method

    repo.update_column(
        column_id,
        pii_category_id=pii_category_id,
        sensitivity_level_id=sensitivity_level_id,
        detection_method=detection_method,
        confidence_score=round(result.confidence, 4),
        sample_values=json.dumps(sample_values[:10], ensure_ascii=False, default=str),
        scanned=True,
    )


# ------------------------------------------------------------------ #
# Pipeline
# ------------------------------------------------------------------ #

def scan_table(
    classifier: PIIClassifier,
    repo: MetadataRepository,
    sampler: DataSampler,
    namespace: str,
    table_name: str,
) -> tuple[int, int, int]:
    """Scan all unscanned columns of one table.

    Returns (scanned, classified, unsure) counts.
    """
    table_meta = repo.get_table_metadata(namespace, table_name)
    if table_meta is None:
        print(f"  [SKIP] No metadata entry for {namespace}.{table_name}")
        return 0, 0, 0

    unscanned = repo.get_unscanned_columns(table_meta.id)
    if not unscanned:
        print(f"  [SKIP] All columns already scanned")
        return 0, 0, 0

    # Collect sample data for the unscanned columns
    col_names = [c.column_name for c in unscanned]
    print(f"  [SAMPLE] Collecting samples for {len(col_names)} columns ...")
    samples_map = sampler.sample_table(namespace, table_name, columns=col_names)

    scanned_count = 0
    classified_count = 0
    unsure_count = 0

    for col_meta in unscanned:
        col_samples = [str(v) for v in samples_map.get(col_meta.column_name, [])]
        result = classifier.classify(col_meta.column_name, col_samples)

        _apply_result(repo, col_meta.id, result, col_samples)
        scanned_count += 1

        if result.pii_category is not None:
            classified_count += 1
            print(
                f"  [PII]  {col_meta.column_name:<25} -> "
                f"{result.pii_category.value:<15} "
                f"(confidence={result.confidence:.2f}, "
                f"method={result.detection_method.value})"
            )
        elif result.detection_method == DetectionMethod.UNKNOWN:
            unsure_count += 1
            print(
                f"  [????] {col_meta.column_name:<25} -> "
                f"UNSURE (confidence={result.confidence:.2f})"
            )
        else:
            print(
                f"  [----] {col_meta.column_name:<25} -> "
                f"NONE"
            )

    return scanned_count, classified_count, unsure_count


def main():
    cfg = load_config()

    # ---- Spark + Iceberg ---------------------------------------------------
    spark = build_spark_session("pii-scanner", cfg)
    catalog_client = CatalogClient(spark, cfg.catalog_name)
    sampler = DataSampler(catalog_client)

    # ---- Metadata store (PostgreSQL) ---------------------------------------
    engine = create_engine_from_config(cfg)
    session = create_session(engine)
    repo = MetadataRepository(session)

    namespace = cfg.namespace

    # ---- Build classifier from DB rules ------------------------------------
    print("=" * 60)
    print("Loading PII detection rules from metadata store ...")
    pii_rules = _build_pii_rules(repo)
    print(f"  Loaded {len(pii_rules)} PII categories")
    print("=" * 60)

    classifier = PIIClassifier(pii_rules)

    # ---- Discover and scan tables ------------------------------------------
    tables = catalog_client.list_tables(namespace)
    print(f"\nFound {len(tables)} table(s) in {cfg.catalog_name}.{namespace}\n")

    total_scanned = 0
    total_classified = 0
    total_unsure = 0

    for table_name in tables:
        print(f"[TABLE] {namespace}.{table_name}")

        try:
            scanned, classified, unsure = scan_table(
                classifier, repo, sampler, namespace, table_name
            )
            total_scanned += scanned
            total_classified += classified
            total_unsure += unsure
            session.commit()
        except Exception as e:
            print(f"  [ERROR] {e}")
            session.rollback()

    # ---- Summary -----------------------------------------------------------
    print("\n" + "=" * 60)
    print("PII Scan Summary")
    print("=" * 60)
    print(f"  Tables processed : {len(tables)}")
    print(f"  Columns scanned  : {total_scanned}")
    print(f"  PII detected     : {total_classified}")
    print(f"  Unsure (for LLM) : {total_unsure}")
    print(f"  Clean (no PII)   : {total_scanned - total_classified - total_unsure}")
    print("=" * 60)

    session.close()
    spark.stop()

    print("\nDone.")


if __name__ == "__main__":
    main()
