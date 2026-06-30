"""
pii_classification — Rule-based PII detection for tabular data.

Usage::

    from pii_classification import PIIClassifier
    from pii_classification.dtos import PIIRule, ClassificationResult
    from core.enums import PIICategory, SensitivityLevel

    rules = [
        PIIRule(
            pii_category=PIICategory.NATIONAL_ID,
            aliases=["cccd", "cmnd", "citizenid"],
            regex_pattern=r"[0-9]{12}",
            default_sensitivity=SensitivityLevel.HIGH,
        ),
        # ... more rules
    ]

    classifier = PIIClassifier(rules)
    result = classifier.classify("citizen_id", ["001234567890", ...])
"""

from pii_classification.dtos import ClassificationResult, PIIRule
from pii_classification.pii_classifier import PIIClassifier

__all__ = [
    "ClassificationResult",
    "PIIClassifier",
    "PIIRule",
]
