"""
Quick test for the pii_classification module.

Run from the spark_jobs directory:
    python test_pii_classification.py
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from core.enums import DetectionMethod, PIICategory, SensitivityLevel
from pii_classification import PIIClassifier, PIIRule, ClassificationResult


# ------------------------------------------------------------------ #
# Test rules (mimicking what the pipeline builds from the DB)
# ------------------------------------------------------------------ #

RULES = [
    PIIRule(
        pii_category=PIICategory.NATIONAL_ID,
        aliases=["cccd", "cmnd", "citizenid", "nationalid", "identitynumber", "personalid"],
        regex_pattern=r"[0-9]{12}",
        default_sensitivity=SensitivityLevel.HIGH,
    ),
    PIIRule(
        pii_category=PIICategory.PHONE,
        aliases=["phone", "phonenumber", "mobile", "mobilephone", "telephone",
                 "tel", "contactnumber", "sdt", "sodienthoai"],
        regex_pattern=r"(03|05|07|08|09)[0-9]{8}",
        default_sensitivity=SensitivityLevel.MEDIUM,
    ),
    PIIRule(
        pii_category=PIICategory.EMAIL,
        aliases=["email", "emailaddress", "mail"],
        regex_pattern=r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        default_sensitivity=SensitivityLevel.MEDIUM,
    ),
    PIIRule(
        pii_category=PIICategory.SALARY,
        aliases=["salary", "wage", "income", "monthlysalary", "annualsalary",
                 "luong", "mucluong"],
        regex_pattern=None,   # no regex for salary
        default_sensitivity=SensitivityLevel.HIGH,
    ),
    PIIRule(
        pii_category=PIICategory.FULL_NAME,
        aliases=["fullname", "name", "customername", "employeename",
                 "citizenname", "personname", "hoten", "hovaten"],
        regex_pattern=None,
        default_sensitivity=SensitivityLevel.MEDIUM,
    ),
    PIIRule(
        pii_category=PIICategory.ADDRESS,
        aliases=["address", "homeaddress", "residentialaddress", "location", "diachi"],
        regex_pattern=None,
        default_sensitivity=SensitivityLevel.LOW,
    ),
]


# ------------------------------------------------------------------ #
# Test helpers
# ------------------------------------------------------------------ #

passed = 0
failed = 0


def check(
    label: str,
    result: ClassificationResult,
    expected_category: PIICategory | None,
    expected_confidence: float | None = None,
    expected_method: DetectionMethod | None = None,
):
    global passed, failed
    errors = []

    if result.pii_category != expected_category:
        errors.append(
            f"category: got {result.pii_category}, expected {expected_category}"
        )

    if expected_confidence is not None:
        if abs(result.confidence - expected_confidence) > 0.01:
            errors.append(
                f"confidence: got {result.confidence:.4f}, "
                f"expected {expected_confidence:.4f}"
            )

    if expected_method is not None:
        if result.detection_method != expected_method:
            errors.append(
                f"method: got {result.detection_method}, expected {expected_method}"
            )

    if errors:
        failed += 1
        print(f"  FAIL  {label}")
        for e in errors:
            print(f"        └─ {e}")
    else:
        passed += 1
        print(f"  PASS  {label}")


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #

def main():
    global passed, failed
    classifier = PIIClassifier(RULES)

    print("=" * 60)
    print("Column-Name Detection Tests")
    print("=" * 60)

    # Perfect match
    r = classifier.classify("cccd", [])
    check("exact alias 'cccd' -> NATIONAL_ID, conf=1.0",
          r, PIICategory.NATIONAL_ID, 1.0, DetectionMethod.MANUAL)

    # Contains match
    r = classifier.classify("so_cccd", [])
    check("contains alias 'so_cccd' -> NATIONAL_ID, conf=0.7",
          r, PIICategory.NATIONAL_ID, 0.7, DetectionMethod.MANUAL)

    # Case insensitive + separators
    r = classifier.classify("Phone_Number", [])
    check("normalized 'Phone_Number' -> PHONE, conf=1.0",
          r, PIICategory.PHONE, 1.0, DetectionMethod.MANUAL)

    # No match -> unsure (conf 0.5 < threshold) -> UNKNOWN
    r = classifier.classify("random_column", [])
    check("no match 'random_column' -> None (UNKNOWN)",
          r, None, 0.0, DetectionMethod.UNKNOWN)

    # Salary (no regex) — column name only
    r = classifier.classify("monthly_salary", [])
    check("salary alias 'monthly_salary' -> SALARY, conf=1.0",
          r, PIICategory.SALARY, 1.0, DetectionMethod.MANUAL)

    print()
    print("=" * 60)
    print("Regex Detection Tests")
    print("=" * 60)

    # 100% match
    samples_100 = [f"{i:012d}" for i in range(100)]
    r = classifier.classify("col_xyz", samples_100)
    check("100% 12-digit numbers -> NATIONAL_ID, conf=1.0",
          r, PIICategory.NATIONAL_ID, 1.0, DetectionMethod.REGEX)

    # 80% phone match
    phones = [f"09{i:08d}" for i in range(80)]
    noise = [f"xxx{i}" for i in range(20)]
    r = classifier.classify("col_abc", phones + noise)
    check("80% phone numbers -> PHONE, conf=0.8",
          r, PIICategory.PHONE, 0.8, DetectionMethod.REGEX)

    # Below threshold — 60% match
    emails = [f"user{i}@example.com" for i in range(60)]
    noise2 = [f"not_email_{i}" for i in range(40)]
    r = classifier.classify("col_data", emails + noise2)
    check("60% emails (below threshold) -> None (UNKNOWN)",
          r, None, 0.6, DetectionMethod.UNKNOWN)

    print()
    print("=" * 60)
    print("Combined Detection Tests")
    print("=" * 60)

    # Same category: column name + regex agree
    samples_cccd = [f"{i:012d}" for i in range(100)]
    r = classifier.classify("citizen_id", samples_cccd)
    # colname: NATIONAL_ID conf=1.0 (exact match "citizenid")
    # regex: NATIONAL_ID conf=1.0
    # combined: 0.8*1.0 + 0.2*1.0 = 1.0
    check("both agree NATIONAL_ID -> HYBRID, conf=1.0",
          r, PIICategory.NATIONAL_ID, 1.0, DetectionMethod.HYBRID)

    # Different categories: column name says one, regex says another
    phone_samples = [f"09{i:08d}" for i in range(100)]
    r = classifier.classify("email", phone_samples)
    # colname: EMAIL (perfect match, conf=1.0)
    # regex: PHONE (conf=1.0)
    # different -> take regex
    check("colname=EMAIL, regex=PHONE -> takes PHONE",
          r, PIICategory.PHONE, 1.0, DetectionMethod.REGEX)

    # Column name only (no regex match)
    r = classifier.classify("ho_va_ten", ["Nguyen Van A", "Tran Thi B", "Le Van C"])
    check("'ho_va_ten' name match, no regex -> FULL_NAME",
          r, PIICategory.FULL_NAME, 1.0, DetectionMethod.MANUAL)

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
