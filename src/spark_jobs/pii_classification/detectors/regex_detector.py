"""
Regex-based PII detector.

Scans sample data values against a regular expression pattern to
determine whether a column likely contains a specific PII category.
"""

from __future__ import annotations

import re

from core.enums import DetectionMethod, PIICategory
from pii_classification.dtos import ClassificationResult


class RegexDetector:
    """Detect PII by matching sample data against a regex pattern.

    Parameters
    ----------
    pii_category : PIICategory
        The PII category this detector checks for.
    regex_pattern : str | None
        The regex pattern string.  When ``None`` the detector always
        returns confidence ``0.0`` (the category has no regex rule).
    """

    def __init__(
        self, pii_category: PIICategory, regex_pattern: str | None
    ) -> None:
        self.pii_category = pii_category
        self._compiled = re.compile(regex_pattern) if regex_pattern else None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def detect(self, samples: list[str]) -> ClassificationResult:
        """Scan *samples* and return a classification result.

        A sample counts as a match if the pattern either fully matches
        (``fullmatch``) or appears as a substring (``search``).

        Returns
        -------
        ClassificationResult
            confidence = matched_count / total_count.
            If ``regex_pattern`` is None, confidence is always ``0.0``.
        """
        if self._compiled is None or not samples:
            return ClassificationResult(
                pii_category=self.pii_category,
                confidence=0.0,
                detection_method=DetectionMethod.REGEX,
                sensitivity=None,
            )

        matched = sum(1 for s in samples if self._is_match(str(s)))
        confidence = matched / len(samples)

        return ClassificationResult(
            pii_category=self.pii_category,
            confidence=confidence,
            detection_method=DetectionMethod.REGEX,
            sensitivity=None,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _is_match(self, value: str) -> bool:
        """Return True if *value* is a full match or contains a match."""
        assert self._compiled is not None
        return (
            self._compiled.fullmatch(value) is not None
            or self._compiled.search(value) is not None
        )
