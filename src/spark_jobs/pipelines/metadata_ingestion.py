"""
Pipeline: Metadata Ingestion

Scans all tables in the Iceberg catalog, extracts schema metadata and sample
data, and writes everything to the metadata store in PostgreSQL.

This is the first stage of the data governance pipeline — it populates the
``tables_metadata`` and ``columns_metadata`` tables so that downstream
modules (AI classifier, Policy Engine) have something to work with.
"""

from __future__ import annotations

import sys

from core.config import load_config
from core.connection import create_engine_from_config, create_session
from core.spark_session import build_spark_session
from metadata_proccessor import CatalogClient, MetadataScanner, DataSampler
from metadata_store import MetadataRepository


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _stringify_samples(values: list) -> list[str]:
    """Convert sample values to strings for JSON storage."""
    return [str(v) for v in values]


def process_table(
    namespace: str,
    table_name: str,
    scanner: MetadataScanner,
    sampler: DataSampler,
    repo: MetadataRepository,
) -> None:
    """Register a single table and its columns in the metadata store.

    Steps:
        1. Register the table (skip if already registered).
        2. Read the schema from Iceberg via ``MetadataScanner``.
        3. For each column not yet in the metadata store, create an entry
           and attach sample values via ``DataSampler``.
    """
    # add table to metadata, if not already existed
    table_meta = repo.get_table_metadata(namespace, table_name)
    if table_meta is None:
        table_meta = repo.create_table_metadata(namespace, table_name)
        print(f"  [NEW]  Registered table {namespace}.{table_name}")
    else:
        print(f"  [SKIP] Table {namespace}.{table_name} already registered")

    # read schema 
    schema_cols = scanner.scan_table(namespace, table_name)

    # insert new columns only, avoid duplicate error when re-running job.
    existing_cols = {
        col.column_name
        for col in repo.get_columns_by_table(table_meta.id)
    }

    # add columns + sample data
    new_col_names = [
        c["column_name"]
        for c in schema_cols
        if c["column_name"] not in existing_cols
    ]

    print("-" * 10)
    print(f"Current Columns: {existing_cols}")
    print(f"New Columns: {new_col_names}")
    print("-" * 10)

    if not new_col_names:
        print(f"         No new columns to register")
        return

    samples = sampler.sample_table(namespace, table_name, columns=new_col_names)

    for col_info in schema_cols:
        col_name = col_info["column_name"]
        if col_name in existing_cols:
            continue

        col_meta = repo.create_column_metadata(
            table_id=table_meta.id,
            column_name=col_name,
            data_type=col_info["data_type"],
        )

        # Attach sample values
        col_samples = samples.get(col_name, [])
        if col_samples:
            repo.update_column(
                col_meta.id,
                sample_values=_stringify_samples(col_samples),
            )

        print(f"         + {col_name} ({col_info['data_type']}"
              f", {len(col_samples)} samples)")


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main():
    cfg = load_config()

    # ---- Spark -----------------------------------------------------------
    spark = build_spark_session("metadata-ingestion", cfg)
    catalog_name = cfg["catalog_name"]
    namespace = cfg["namespace"]

    # ---- Metadata processor components -----------------------------------
    catalog_client = CatalogClient(spark, catalog_name)
    scanner = MetadataScanner(catalog_client)
    sampler = DataSampler(catalog_client)

    # ---- Metadata store --------------------------------------------------
    engine = create_engine_from_config(cfg)
    session = create_session(engine)
    repo = MetadataRepository(session)

    # ---- Run -------------------------------------------------------------
    print("=" * 60)
    print("Metadata Ingestion Pipeline")
    print("=" * 60)

    tables = catalog_client.list_tables(namespace)
    print(f"\nFound {len(tables)} table(s) in {catalog_name}.{namespace}\n")

    success = 0
    errors = 0

    for table_name in tables:
        try:
            print(f"[TABLE] {namespace}.{table_name}")
            process_table(namespace, table_name, scanner, sampler, repo)
            session.commit()
            success += 1
        except Exception as exc:
            session.rollback()
            print(f"  [ERROR] {exc}")
            errors += 1

    print()
    print("=" * 60)
    print(f"Done: {success} succeeded, {errors} failed")
    print("=" * 60)

    session.close()
    spark.stop()

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()