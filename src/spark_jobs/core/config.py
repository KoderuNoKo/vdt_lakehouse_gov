"""
Centralized configuration loader for Spark jobs.

All connection details and paths are read from environment variables,
which are injected into the Spark containers via `env_file: .env`
in docker-compose.yml.

Every variable has a sensible default so jobs still work when
env vars are not explicitly set (matching the current docker-compose
defaults).
"""

import os


def load_config() -> dict:
    """Load configuration from environment variables.

    Returns a dict with all connection details, paths, and catalog settings
    needed by the Spark jobs.  Derived values (JDBC URL, MinIO endpoint)
    are computed from the base env vars.
    """

    db_host   = os.getenv("DB_HOST_CONTAINER", "postgres")
    db_port   = os.getenv("DB_PORT_CONTAINER", "5432")
    db_name   = os.getenv("DB_NAME", "pg_iceberg")
    db_schema = os.getenv("DB_SCHEMA", "ib_catalog")
    db_user   = os.getenv("DB_USER", "postgres")
    db_pass   = os.getenv("DB_PASSWORD", "postgres")

    lh_host = os.getenv("LH_HOST_CONTAINER", "minio")
    lh_port = os.getenv("LH_PORT_CONTAINER_API", "9000")
    lh_user = os.getenv("LH_USER", "minio")
    lh_pass = os.getenv("LH_PASSWORD", "minio_password")

    return {
        # ---- Iceberg catalog ------------------------------------------------
        "catalog_name":   os.getenv("ICEBERG_CATALOG_NAME", "lakehouse"),
        "namespace":      os.getenv("ICEBERG_NAMESPACE", "raw"),

        # ---- PostgreSQL (Iceberg JDBC catalog backend) ----------------------
        "db_host":        db_host,
        "db_port":        db_port,
        "db_name":        db_name,
        "db_schema":      db_schema,
        "db_user":        db_user,
        "db_password":    db_pass,
        "jdbc_url":       (
            f"jdbc:postgresql://{db_host}:{db_port}"
            f"/{db_name}?currentSchema={db_schema}"
        ),

        # ---- MinIO / S3A (Iceberg warehouse storage) ------------------------
        "lh_host":        lh_host,
        "lh_port":        lh_port,
        "lh_user":        lh_user,
        "lh_password":    lh_pass,
        "lh_endpoint":    f"http://{lh_host}:{lh_port}",
        "warehouse_path": os.getenv("WAREHOUSE_PATH", "s3a://lakehouse/"),

        # ---- Data paths -----------------------------------------------------
        "csv_dir":        os.getenv("CSV_DIR", "/opt/spark/data/csv"),
    }
