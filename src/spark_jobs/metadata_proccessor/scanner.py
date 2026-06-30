"""
Metadata extraction utilities for Iceberg tables.

- ``MetadataScanner``: reads table schema and returns structured column info.
- ``DataSampler``: collects representative sample values from columns.

Both classes take a ``CatalogClient`` so they never touch Spark SQL directly.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from metadata_proccessor.catalog_client import CatalogClient


# Default number of sample rows to collect per column.
DEFAULT_SAMPLE_SIZE = 50


class MetadataScanner:
    """Scan Iceberg tables for their schema metadata."""

    def __init__(self, catalog_client: CatalogClient) -> None:
        self.catalog = catalog_client

    def scan_table(self, namespace: str, table_name: str) -> list[dict]:
        """Read the schema of a table and return column metadata.

        Returns a list of dicts, one per column::

            [
                {"column_name": "cccd", "data_type": "StringType"},
                {"column_name": "age",  "data_type": "IntegerType"},
                ...
            ]
        """
        return self.catalog.get_schema(namespace, table_name)


class DataSampler:
    """Collect representative sample values from table columns."""

    def __init__(self, catalog_client: CatalogClient) -> None:
        self.catalog = catalog_client

    def sample_column(
        self,
        df: DataFrame,
        column_name: str,
        sample_size: int = DEFAULT_SAMPLE_SIZE,
    ) -> list:
        """Collect up to *sample_size* distinct non-null values from a column.

        Returns a plain Python list of values (strings, ints, etc.).
        """
        sample_rows = (
            df.select(column_name)
            .where(F.col(column_name).isNotNull())
            .distinct()
            .limit(sample_size)
            .collect()
        )
        return [row[0] for row in sample_rows]

    def sample_table(
        self,
        namespace: str,
        table_name: str,
        columns: list[str] | None = None,
        sample_size: int = DEFAULT_SAMPLE_SIZE,
    ) -> dict[str, list]:
        """Collect sample values for every column (or a subset) of a table.

        Returns a dict mapping ``column_name -> [sample_values]``.
        """
        df = self.catalog.load_table(namespace, table_name)

        if columns is None:
            columns = [field.name for field in df.schema.fields]

        return {
            col: self.sample_column(df, col, sample_size)
            for col in columns
        }