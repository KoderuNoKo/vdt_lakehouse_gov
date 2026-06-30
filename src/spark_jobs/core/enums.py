"""
Enums for seeded / fixed reference values in the metadata store.

These mirror the seed data in ``docker/postgres/07_CreateMetadataStore.sql``.
Any module that needs to reference a sensitivity level, PII category, role,
masking function, detection method, or policy action should import from here
rather than using raw strings.
"""

import enum


#! used by postgres enum type
class DetectionMethod(enum.Enum):
    """How a column's PII category was determined."""
    REGEX = "REGEX"
    LLM = "LLM"
    HYBRID = "HYBRID"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


#! used by postgres enum type
class PolicyAction(enum.Enum):
    """What to do when a role accesses a sensitive column."""
    ALLOW = "ALLOW"
    MASK = "MASK"
    DENY = "DENY"
    

class SensitivityLevel(enum.Enum):
    """Sensitivity classification for a column."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class RoleName(enum.Enum):
    """User roles in the access-control model."""
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"


class MaskingFunction(enum.Enum):
    """Available masking strategies."""
    PARTIAL_MASK = "PARTIAL_MASK"
    HASH_MASK = "HASH_MASK"
    REDACT = "REDACT"
    NULLIFY = "NULLIFY"


class PIICategory(enum.Enum):
    """Types of Personally Identifiable Information tracked by the system."""
    NATIONAL_ID = "NATIONAL_ID"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    TAX_CODE = "TAX_CODE"
    SALARY = "SALARY"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    FULL_NAME = "FULL_NAME"
    ADDRESS = "ADDRESS"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    WORKPLACE = "WORKPLACE"
