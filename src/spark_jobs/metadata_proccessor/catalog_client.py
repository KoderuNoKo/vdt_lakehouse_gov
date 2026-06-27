"""
A clean, unified interface for interacting with the Iceberg catalog via Spark.

Wraps Spark SQL calls for listing namespaces/tables and loading DataFrames
so that the rest of the codebase does not need to know about Spark SQL syntax.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession


class CatalogClient:
    """Read-only client for browsing the Iceberg catalog."""

    def __init__(self, spark: SparkSession, catalog_name: str) -> None:
        self.spark = spark
        self.catalog = catalog_name

    def list_namespaces(self) -> list[str]:
        """Return all namespaces (databases) in the catalog."""
        rows = self.spark.sql(
            f"SHOW NAMESPACES IN {self.catalog}"
        ).collect()
        return [row[0] for row in rows]

    def list_tables(self, namespace: str) -> list[str]:
        """Return the names of all tables in a namespace."""
        rows = self.spark.sql(
            f"SHOW TABLES IN {self.catalog}.{namespace}"
        ).collect()
        return [row["tableName"] for row in rows]

    def load_table(self, namespace: str, table_name: str) -> DataFrame:
        """Load a table as a Spark DataFrame."""
        full_name = f"{self.catalog}.{namespace}.{table_name}"
        return self.spark.table(full_name)

    def get_schema(self, namespace: str, table_name: str) -> list[dict]:
        """Return the schema of a table as a list of ``{name, type}`` dicts.

        Uses the DataFrame schema directly — no SQL parsing needed.
        """
        df = self.load_table(namespace, table_name)
        return [
            {"column_name": field.name, "data_type": str(field.dataType)}
            for field in df.schema.fields
        ]