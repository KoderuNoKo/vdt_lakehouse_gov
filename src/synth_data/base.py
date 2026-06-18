"""Base class for all table generators."""

from abc import ABC, abstractmethod

import pandas as pd
from faker import Faker


class TableGenerator(ABC):
    """Abstract base for synthetic table generators.

    Subclasses must implement:
        - ``table_name``  (class attribute)
        - ``columns``     (class attribute — list of column names)
        - ``_generate_row()`` — returns a dict for one row
    """

    table_name: str = ""
    columns: list[str] = []

    def __init__(self, locale: str | list[str] = "vi_VN", seed: int | None = None):
        self.fake = Faker(locale)
        if seed is not None:
            Faker.seed(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, n: int = 100) -> pd.DataFrame:
        """Generate *n* rows and return a DataFrame."""
        rows = [self._generate_row(i) for i in range(n)]
        return pd.DataFrame(rows, columns=self.columns)

    def to_csv(self, path: str, n: int = 100, **kwargs) -> None:
        """Generate and write to CSV."""
        df = self.generate(n)
        df.to_csv(path, index=False, **kwargs)

    def to_parquet(self, path: str, n: int = 100, **kwargs) -> None:
        """Generate and write to Parquet."""
        df = self.generate(n)
        df.to_parquet(path, index=False, **kwargs)

    # ------------------------------------------------------------------
    # Subclass hook
    # ------------------------------------------------------------------
    @abstractmethod
    def _generate_row(self, index: int) -> dict:
        """Return a single row as a dict.

        Args:
            index: 0-based row index (useful for sequential IDs).
        """
        ...
