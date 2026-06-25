"""
SQLAlchemy ORM models for the ``ib_metadata`` schema.

These models mirror the DDL in ``docker/postgres/07_CreateMetadataStore.sql``
exactly.  They are used for DML and DQL only — DDL is owned by the SQL
init script and must remain the single source of truth.

**Do not call** ``Base.metadata.create_all()`` in production code.
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, relationship


# ============================================================
# Base
# ============================================================

SCHEMA = "ib_metadata"


class Base(DeclarativeBase):
    pass


# ============================================================
# PostgreSQL ENUMs
# ============================================================
# The types already exist in the database (created by the DDL script),
# so we set ``create_type=False`` to prevent SQLAlchemy from attempting
# to issue ``CREATE TYPE`` statements.

class DetectionMethodEnum(enum.Enum):
    REGEX = "REGEX"
    LLM = "LLM"
    HYBRID = "HYBRID"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


class PolicyActionEnum(enum.Enum):
    ALLOW = "ALLOW"
    MASK = "MASK"
    DENY = "DENY"


detection_method_type = Enum(
    DetectionMethodEnum,
    name="detection_method_enum",
    schema=SCHEMA,
    create_type=False,
)

policy_action_type = Enum(
    PolicyActionEnum,
    name="policy_action_enum",
    schema=SCHEMA,
    create_type=False,
)


# ============================================================
# Reference / Lookup Tables
# ============================================================

class SensitivityLevel(Base):
    """``ib_metadata.sensitivity_levels`` — HIGH / MEDIUM / LOW / NONE."""

    __tablename__ = "sensitivity_levels"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text)


class PIICategory(Base):
    """``ib_metadata.pii_categories`` — NATIONAL_ID, PHONE, EMAIL, …"""

    __tablename__ = "pii_categories"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    regex_pattern = Column(Text)
    default_sensitivity_level_id = Column(
        Integer,
        ForeignKey(f"{SCHEMA}.sensitivity_levels.id"),
    )

    # relationships
    default_sensitivity_level = relationship(
        "SensitivityLevel", foreign_keys=[default_sensitivity_level_id]
    )


class Role(Base):
    """``ib_metadata.roles`` — ADMIN, ANALYST, AUDITOR."""

    __tablename__ = "roles"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class MaskingFunction(Base):
    """``ib_metadata.masking_functions`` — PARTIAL_MASK, HASH_MASK, …"""

    __tablename__ = "masking_functions"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, autoincrement=True)
    function_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


# ============================================================
# Core Metadata Tables
# ============================================================

class TableMetadata(Base):
    """``ib_metadata.tables_metadata`` — one row per Iceberg table."""

    __tablename__ = "tables_metadata"
    __table_args__ = (
        UniqueConstraint("namespace", "table_name"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    namespace = Column(String(255), nullable=False)
    table_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    # relationships
    columns = relationship(
        "ColumnMetadata",
        back_populates="table",
        cascade="all, delete-orphan",
    )


class ColumnMetadata(Base):
    """``ib_metadata.columns_metadata`` — one row per column per table."""

    __tablename__ = "columns_metadata"
    __table_args__ = (
        UniqueConstraint("table_id", "column_name"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_id = Column(
        Integer,
        ForeignKey(f"{SCHEMA}.tables_metadata.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)
    pii_category_id = Column(
        Integer, ForeignKey(f"{SCHEMA}.pii_categories.id")
    )
    sensitivity_level_id = Column(
        Integer, ForeignKey(f"{SCHEMA}.sensitivity_levels.id")
    )
    detection_method = Column(detection_method_type)
    confidence_score = Column(Numeric(5, 4))
    sample_values = Column(JSONB)
    scanned = Column(Boolean, server_default="FALSE")
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    # relationships
    table = relationship("TableMetadata", back_populates="columns")
    pii_category = relationship("PIICategory", foreign_keys=[pii_category_id])
    sensitivity_level = relationship(
        "SensitivityLevel", foreign_keys=[sensitivity_level_id]
    )


# ============================================================
# Access Control
# ============================================================

class AccessPolicy(Base):
    """``ib_metadata.access_policies`` — maps (role, sensitivity) → action."""

    __tablename__ = "access_policies"
    __table_args__ = (
        UniqueConstraint("role_id", "sensitivity_level_id"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(
        Integer,
        ForeignKey(f"{SCHEMA}.roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    sensitivity_level_id = Column(
        Integer,
        ForeignKey(f"{SCHEMA}.sensitivity_levels.id"),
        nullable=False,
    )
    action = Column(policy_action_type, nullable=False)
    masking_function_id = Column(
        Integer, ForeignKey(f"{SCHEMA}.masking_functions.id")
    )
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    # relationships
    role = relationship("Role", foreign_keys=[role_id])
    sensitivity_level = relationship(
        "SensitivityLevel", foreign_keys=[sensitivity_level_id]
    )
    masking_function = relationship(
        "MaskingFunction", foreign_keys=[masking_function_id]
    )