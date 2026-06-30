"""
Column-name-based PII detector.

Matches a column name against a list of known aliases for a specific
PII category.  Aliases are expected to already be in normalized form
(lowercase, no separators).
"""

from __future__ import annotations

import re

from core.enums import DetectionMethod, PIICategory
from pii_classification.dtos import ClassificationResult


# Pattern that matches any separator character (space, hyphen, underscore,
# dot, or any other non-alphanumeric character).
_SEPARATOR_RE = re.compile(r"[^a-z0-9]")


class ColumnNameDetector:
    """Detect PII by matching a column name against known aliases.

    Parameters
    ----------
    pii_category : PIICategory
        The PII category this detector checks for.
    aliases : list[str]
        Normalized alias strings (lowercase, no separators).
    """

    def __init__(self, pii_category: PIICategory, aliases: list[str]) -> None:
        self.pii_category = pii_category
        self.aliases = aliases

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def detect(self, column_name: str) -> ClassificationResult:
        """Check *column_name* against this detector's aliases.

        Two passes are made (exact before contains) so that alias ordering
        does not affect the result.

        Returns
        -------
        ClassificationResult
            - Perfect match  -> confidence ``1.0``
            - Contains alias -> confidence ``0.7``
            - No match       -> ``pii_category=None``, confidence ``0.5``
        """
        normalized = self.normalize(column_name)

        # Pass 1: exact match (highest priority)
        for alias in self.aliases:
            if normalized == alias:
                return ClassificationResult(
                    pii_category=self.pii_category,
                    confidence=1.0,
                    detection_method=DetectionMethod.MANUAL,
                    sensitivity=None,
                )

        # Pass 2: contains match (stop on first)
        for alias in self.aliases:
            if alias in normalized:
                return ClassificationResult(
                    pii_category=self.pii_category,
                    confidence=0.7,
                    detection_method=DetectionMethod.MANUAL,
                    sensitivity=None,
                )

        # No match for this category
        return ClassificationResult(
            pii_category=None,
            confidence=0.5,
            detection_method=DetectionMethod.MANUAL,
            sensitivity=None,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def normalize(name: str) -> str:
        """Lowercase and strip all separator characters.

        >>> ColumnNameDetector.normalize("Citizen_ID")
        'citizenid'
        >>> ColumnNameDetector.normalize("ho va ten")
        'hovaten'
        """
        return _SEPARATOR_RE.sub("", name.lower())
