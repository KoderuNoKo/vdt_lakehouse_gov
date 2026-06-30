"""
PII Classifier — the main orchestrator for the pii_classification module.

Given a column name and sample data, runs both detection strategies
(column-name matching and regex scanning) across all configured PII rules,
then combines the results into a single :class:`ClassificationResult`.
"""

from __future__ import annotations

from core.enums import DetectionMethod, SensitivityLevel
from pii_classification.detectors import ColumnNameDetector, RegexDetector
from pii_classification.dtos import ClassificationResult, PIIRule


class PIIClassifier:
    """Classify a column's PII category using rule-based detection.

    Parameters
    ----------
    pii_rules : list[PIIRule]
        Detection configuration for every known PII category.  Typically
        built from the ``pii_categories`` table by the pipeline.

    Example
    -------
    ::

        rules = [
            PIIRule(
                pii_category=PIICategory.NATIONAL_ID,
                aliases=["cccd", "cmnd", "citizenid", ...],
                regex_pattern=r"[0-9]{12}",
                default_sensitivity=SensitivityLevel.HIGH,
            ),
            ...
        ]
        classifier = PIIClassifier(rules)
        result = classifier.classify("citizen_id", ["001234567890", ...])
    """

    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, pii_rules: list[PIIRule]) -> None:
        self.rules = pii_rules

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def classify(
        self, column_name: str, samples: list[str]
    ) -> ClassificationResult:
        """Classify a single column.

        Parameters
        ----------
        column_name : str
            The original column name (will be normalized internally).
        samples : list[str]
            Representative sample values from the column.

        Returns
        -------
        ClassificationResult
            The combined detection result.  If the final confidence is
            below :attr:`CONFIDENCE_THRESHOLD` the result is marked as
            ``UNKNOWN`` (unsure) — ready for a future LLM pass.
        """
        colname_result = self._best_column_name_match(column_name)
        regex_result = self._best_regex_match(samples)
        combined = self._combine(colname_result, regex_result)
        return combined

    # ------------------------------------------------------------------ #
    # Detection passes
    # ------------------------------------------------------------------ #

    def _best_column_name_match(
        self, column_name: str
    ) -> ClassificationResult:
        """Run column-name detection across all rules, return first match.

        "First match" means the first rule whose aliases produce a
        confidence above the no-match baseline (0.5).  This follows the
        "stop on first match" requirement.
        """
        no_match = ClassificationResult(
            pii_category=None,
            confidence=0.5,
            detection_method=DetectionMethod.MANUAL,
            sensitivity=None,
        )

        for rule in self.rules:
            detector = ColumnNameDetector(rule.pii_category, rule.aliases)
            result = detector.detect(column_name)
            if result.pii_category is not None:
                # Attach sensitivity from the rule
                result.sensitivity = rule.default_sensitivity
                return result

        return no_match

    def _best_regex_match(self, samples: list[str]) -> ClassificationResult:
        """Run regex detection across all rules, return highest confidence.

        Scans every PII category's regex against the samples and picks
        the one with the highest match ratio.
        """
        best = ClassificationResult(
            pii_category=None,
            confidence=0.0,
            detection_method=DetectionMethod.REGEX,
            sensitivity=None,
        )

        for rule in self.rules:
            detector = RegexDetector(rule.pii_category, rule.regex_pattern)
            result = detector.detect(samples)
            if result.confidence > best.confidence:
                result.sensitivity = rule.default_sensitivity
                best = result

        return best

    # ------------------------------------------------------------------ #
    # Combining logic
    # ------------------------------------------------------------------ #

    def _combine(
        self,
        colname: ClassificationResult,
        regex: ClassificationResult,
    ) -> ClassificationResult:
        """Merge column-name and regex results into a final classification.

        Rules:
        1. Same category -> weighted average (0.8 * regex + 0.2 * colname).
        2. Different categories -> take the regex result.
        3. Column-name matched but regex found nothing -> take colname result.
        4. Neither found anything -> NONE / unsure.
        5. Final confidence < CONFIDENCE_THRESHOLD -> mark as UNKNOWN.
        """
        colname_matched = colname.pii_category is not None
        regex_matched = regex.confidence > 0.0

        # Case 4: neither found anything
        if not colname_matched and not regex_matched:
            return ClassificationResult(
                pii_category=None,
                confidence=0.0,
                detection_method=DetectionMethod.UNKNOWN,
                sensitivity=None,
            )

        # Case 3: only column name matched
        if colname_matched and not regex_matched:
            result = ClassificationResult(
                pii_category=colname.pii_category,
                confidence=colname.confidence,
                detection_method=DetectionMethod.MANUAL,
                sensitivity=colname.sensitivity,
            )
            return self._apply_threshold(result)

        # Case: only regex matched (column name found nothing)
        if not colname_matched and regex_matched:
            result = ClassificationResult(
                pii_category=regex.pii_category,
                confidence=regex.confidence,
                detection_method=DetectionMethod.REGEX,
                sensitivity=regex.sensitivity,
            )
            return self._apply_threshold(result)

        # Both matched
        assert colname_matched and regex_matched

        # Case 1: same category -> weighted average
        if colname.pii_category == regex.pii_category:
            combined_confidence = (
                0.8 * regex.confidence + 0.2 * colname.confidence
            )
            result = ClassificationResult(
                pii_category=regex.pii_category,
                confidence=combined_confidence,
                detection_method=DetectionMethod.HYBRID,
                sensitivity=regex.sensitivity,
            )
            return self._apply_threshold(result)

        # Case 2: different categories -> take regex
        result = ClassificationResult(
            pii_category=regex.pii_category,
            confidence=regex.confidence,
            detection_method=DetectionMethod.REGEX,
            sensitivity=regex.sensitivity,
        )
        return self._apply_threshold(result)

    def _apply_threshold(
        self, result: ClassificationResult
    ) -> ClassificationResult:
        """If confidence is below the threshold, mark as UNKNOWN (unsure)."""
        if result.confidence < self.CONFIDENCE_THRESHOLD:
            return ClassificationResult(
                pii_category=None,
                confidence=result.confidence,
                detection_method=DetectionMethod.UNKNOWN,
                sensitivity=None,
            )
        return result