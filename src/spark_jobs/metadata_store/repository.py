"""
A clean, unified API to interact with the metadata store in the database.

Usage::

    from core.connection import create_engine_from_config, create_session
    from metadata_store import MetadataRepository

    engine = create_engine_from_config()
    session = create_session(engine)
    repo = MetadataRepository(session)

    table = repo.create_table_metadata("test", "citizens")
    repo.create_column_metadata(table.id, "cccd", "string")
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from metadata_store.model import (
    AccessPolicy,
    ColumnMetadata,
    MaskingFunctionModel,
    PIICategoryModel,
    PiiScanRecord,
    Role,
    SensitivityLevelModel,
    TableMetadata,
)


class MetadataRepository:
    """Thin wrapper around the ``ib_metadata`` schema.

    Each method maps to a single, clearly-scoped operation on the metadata
    store.  The caller is responsible for committing or rolling back the
    session.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------ #
    # tables_metadata
    # ------------------------------------------------------------------ #

    def create_table_metadata(
        self, namespace: str, table_name: str
    ) -> TableMetadata:
        """Add metadata for a new table (new entry in ``tables_metadata``).

        Returns the newly created row.
        """
        entry = TableMetadata(namespace=namespace, table_name=table_name)
        self.session.add(entry)
        self.session.flush()
        return entry

    def get_table_metadata(
        self, namespace: str, table_name: str
    ) -> TableMetadata | None:
        """Get the metadata of a table by namespace and name."""
        return (
            self.session.query(TableMetadata)
            .filter_by(namespace=namespace, table_name=table_name)
            .first()
        )

    # ------------------------------------------------------------------ #
    # columns_metadata
    # ------------------------------------------------------------------ #

    def create_column_metadata(
        self, table_id: int, column_name: str, data_type: str
    ) -> ColumnMetadata:
        """Add metadata for a new column (new entry in ``columns_metadata``)."""
        entry = ColumnMetadata(
            table_id=table_id,
            column_name=column_name,
            data_type=data_type,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def get_columns_by_table(self, table_id: int) -> list[ColumnMetadata]:
        """Get the metadata of all columns of a table."""
        return (
            self.session.query(ColumnMetadata)
            .filter_by(table_id=table_id)
            .all()
        )

    def get_unscanned_columns(self, table_id: int) -> list[ColumnMetadata]:
        """Get columns that have not yet been scanned for PII."""
        return (
            self.session.query(ColumnMetadata)
            .filter_by(table_id=table_id, scanned=False)
            .all()
        )

    def update_column(self, column_id: int, **attributes) -> ColumnMetadata:
        """Update the metadata for an existing column.

        Accepts arbitrary keyword arguments matching ``ColumnMetadata``
        column names (e.g. ``pii_category_id``, ``sensitivity_level_id``,
        ``detection_method``, ``confidence_score``, ``sample_values``,
        ``scanned``).
        """
        entry = self.session.get(ColumnMetadata, column_id)
        if entry is None:
            raise ValueError(f"Column with id={column_id} not found")
        for key, value in attributes.items():
            setattr(entry, key, value)
        self.session.flush()
        return entry

    def add_scan_record(
        self,
        column_id: int,
        detection_method,
        confidence_score,
        detected_category_id: int | None,
    ) -> PiiScanRecord:
        """Add a historical record of a PII scan to ``pii_scan_record``."""
        record = PiiScanRecord(
            column_id=column_id,
            detection_method=detection_method,
            confidence_score=confidence_score,
            detected_category_id=detected_category_id,
        )
        self.session.add(record)
        self.session.flush()
        return record

    # ------------------------------------------------------------------ #
    # access_policies
    # ------------------------------------------------------------------ #

    def get_access_policy(
        self, role_id: int, sensitivity_level_id: int
    ) -> AccessPolicy | None:
        """Get the access policy for a given role and sensitivity level."""
        return (
            self.session.query(AccessPolicy)
            .filter_by(
                role_id=role_id,
                sensitivity_level_id=sensitivity_level_id,
            )
            .first()
        )

    # ------------------------------------------------------------------ #
    # lookups (reference / seed tables)
    # ------------------------------------------------------------------ #

    def get_sensitivity_level(self, code: str) -> SensitivityLevelModel | None:
        """Look up a sensitivity level by its code (e.g. ``'HIGH'``)."""
        return (
            self.session.query(SensitivityLevelModel)
            .filter_by(code=code)
            .first()
        )

    def get_pii_category(self, code: str) -> PIICategoryModel | None:
        """Look up a PII category by its code (e.g. ``'NATIONAL_ID'``)."""
        return (
            self.session.query(PIICategoryModel)
            .filter_by(code=code)
            .first()
        )

    def get_all_pii_categories(self) -> list[PIICategoryModel]:
        """Return all PII categories (with their regex patterns)."""
        return self.session.query(PIICategoryModel).all()

    def get_masking_function(
        self, function_name: str
    ) -> MaskingFunctionModel | None:
        """Look up a masking function by name (e.g. ``'PARTIAL_MASK'``)."""
        return (
            self.session.query(MaskingFunctionModel)
            .filter_by(function_name=function_name)
            .first()
        )

    def get_role(self, role_name: str) -> Role | None:
        """Look up a role by name (e.g. ``'ANALYST'``)."""
        return (
            self.session.query(Role)
            .filter_by(role_name=role_name)
            .first()
        )