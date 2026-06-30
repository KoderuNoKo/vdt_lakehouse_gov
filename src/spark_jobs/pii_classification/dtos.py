"""
Data transfer objects for the pii_classification module.

These are the module's input/output contracts — plain dataclasses with
no database or framework dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.enums import DetectionMethod, PIICategory, SensitivityLevel


# ------------------------------------------------------------------ #
# Input: what the classifier needs to know about each PII category
# ------------------------------------------------------------------ #

@dataclass(frozen=True)
class PIIRule:
    """One PII category's detection configuration.

    Built from ``pii_categories`` rows by the pipeline and handed to
    :class:`PIIClassifier` so it has zero DB awareness.
    """
    pii_category: PIICategory
    aliases: list[str]                  # normalized column-name aliases
    regex_pattern: str | None           # regex for sample-data matching
    default_sensitivity: SensitivityLevel


# ------------------------------------------------------------------ #
# Output: what the classifier returns for a single column
# ------------------------------------------------------------------ #

@dataclass
class ClassificationResult:
    """Result of classifying a single column for PII content."""
    pii_category: PIICategory | None    # None -> not PII / unsure
    confidence: float
    detection_method: DetectionMethod
    sensitivity: SensitivityLevel | None  # carried from the matched PIIRule