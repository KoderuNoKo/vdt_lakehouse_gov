"""
Spark job: Ingest CSV files into Iceberg tables on MinIO.

Reads all CSV files from the configured CSV directory and writes each one
as an Iceberg table under the configured namespace.
"""

import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql import types as T
from pyspark.sql import functions as F

from core.config import load_config, Config
from core.spark_session import build_spark_session
from ingest_data.tables_schema import SCHEMAS


# ---------------------------------------------------------------------------
# Ingestion logic
# ---------------------------------------------------------------------------

def ingest_table(
    spark: SparkSession,
    table_name: str,
    schema: T.StructType,
    cfg: Config,
):
    """Read a single CSV and write it as an Iceberg table."""

    csv_path = os.path.join(cfg.csv_dir, f"{table_name}.csv")

    if not os.path.isfile(csv_path):
        print(f"[SKIP] File not found: {csv_path}")
        return

    print(f"[READ] {csv_path}")
    df = (
        spark.read
        .option("header", "true")
        .option("encoding", "UTF-8")
        .schema(schema)
        .csv(csv_path)
    )

    row_count = df.count()
    print(f"       -> {row_count} rows loaded")

    # Add ingestion metadata
    df = df.withColumn("_ingested_at", F.current_timestamp())

    # Full table name: <catalog>.<namespace>.<table_name>
    full_table = f"{cfg.catalog_name}.{cfg.namespace}.{table_name}"

    print(f"[WRITE] {full_table}")
    (
        df.writeTo(full_table)
        .using("iceberg")
        .tableProperty("format-version", "2")
        .createOrReplace()
    )
    print(f"[DONE] {full_table} — {row_count} rows written\n")


def main():
    cfg   = load_config()
    spark = build_spark_session("ingest-csv-to-iceberg", cfg)

    catalog   = cfg.catalog_name
    namespace = cfg.namespace

    # Create the raw namespace if it does not exist
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {catalog}.{namespace}")

    success_count = 0
    fail_count = 0

    for table_name, schema in SCHEMAS.items():
        try:
            ingest_table(spark, table_name, schema, cfg)
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to ingest {table_name}: {e}")
            fail_count += 1

    print("=" * 60)
    print(f"Ingestion complete: {success_count} succeeded, {fail_count} failed")
    print("=" * 60)

    spark.stop()

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
