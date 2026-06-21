"""
Shared Spark session builder for Iceberg + S3A (MinIO).

Provides a single `build_spark_session()` function that every job
imports, so session configuration is never duplicated.
"""

from pyspark.sql import SparkSession


def build_spark_session(app_name: str, config: dict) -> SparkSession:
    """Create a SparkSession configured for the lakehouse Iceberg catalog.

    Parameters
    ----------
    app_name : str
        The Spark application name.
    config : dict
        Configuration dict returned by ``modules.config.load_config()``.

    Returns
    -------
    SparkSession
    """

    catalog = config["catalog_name"]

    return (
        SparkSession.builder
        .appName(app_name)

        # --- Iceberg catalog -------------------------------------------------
        .config(
            f"spark.sql.catalog.{catalog}",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        .config(
            f"spark.sql.catalog.{catalog}.type",
            "jdbc",
        )
        .config(
            f"spark.sql.catalog.{catalog}.uri",
            config["jdbc_url"],
        )
        .config(
            f"spark.sql.catalog.{catalog}.jdbc.user",
            config["db_user"],
        )
        .config(
            f"spark.sql.catalog.{catalog}.jdbc.password",
            config["db_password"],
        )
        .config(
            f"spark.sql.catalog.{catalog}.warehouse",
            config["warehouse_path"],
        )

        # --- S3A / MinIO -----------------------------------------------------
        .config("spark.hadoop.fs.s3a.endpoint",          config["lh_endpoint"])
        .config("spark.hadoop.fs.s3a.access.key",        config["lh_user"])
        .config("spark.hadoop.fs.s3a.secret.key",        config["lh_password"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem",
        )

        # --- General Iceberg settings ----------------------------------------
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config("spark.sql.defaultCatalog", catalog)

        .getOrCreate()
    )
