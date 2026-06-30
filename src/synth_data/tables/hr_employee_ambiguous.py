"""
Generator for the HR employee table with ambiguous columns.
- contains ambiguous columns

Purpose:
    - weak column names (c01, c02, num_val_1, etc.)
    - relies heavily on LLM for sensitivity
    - (*) push the limit by having multiple columns with similar format data but different meaning
"""

import random
import re

import psycopg2

from synth_data.base import TableGenerator
from synth_data.tables.settings import _DB_CONFIG


class HrEmployeeAmbiguousGenerator(TableGenerator):
    """Generates synthetic HR employee records with ambiguous column names.

    Column mapping:
        c01 -> employee name
        c02 -> salary (VND)
        c03 -> bank account number
        c04 -> tax code (MST)
        c05 -> emergency phone number
    """

    table_name = "hr_employee"
    columns = [
        "employee_id",
        "department",
        "job_title",
        "c01",
        "c02",
        "c03",
        "c04",
        "c05",
        "remarks",
    ]

    # Cached DB data — loaded once across all instances.
    _departments_pool: list[str] | None = None
    _remarks_pool: list[dict] | None = None

    # ------------------------------------------------------------------ #
    # Row generation
    # ------------------------------------------------------------------ #
    def _generate_row(self, index: int) -> dict:
        return {
            "employee_id": index + 1,
            "department": self._generate_department(),
            "job_title": self._generate_job_title(),
            "c01": self._generate_employee_name(),
            "c02": self._generate_salary(),
            "c03": self._generate_bank_account(),
            "c04": self._generate_tax_id(),
            "c05": self._generate_emergency_phone(),
            "remarks": self._generate_remarks(),
        }

    # ------------------------------------------------------------------ #
    # Column generators
    # ------------------------------------------------------------------ #
    def _generate_department(self) -> str:
        pool = self._load_departments_pool()
        return random.choice(pool)

    def _generate_job_title(self) -> str:
        return self.fake.job()

    def _generate_employee_name(self) -> str:
        """c01 — employee full name."""
        return self.fake.name()

    def _generate_salary(self) -> float:
        """c02 — monthly salary in VND (5M–80M range)."""
        return round(random.uniform(5_000_000, 80_000_000), -3)

    def _generate_bank_account(self) -> str:
        """c03 — bank account number (10-14 digits)."""
        length = random.choice([10, 12, 13, 14])
        return self.fake.numerify("#" * length)

    def _generate_tax_id(self) -> str:
        """c04 — personal tax code (MST), 10 or 13 digits."""
        if random.random() < 0.8:
            return self.fake.numerify("##########")
        return self.fake.numerify("#########-###")

    def _generate_emergency_phone(self) -> str:
        """c05 — emergency contact phone number."""
        prefixes = ["03", "05", "07", "08", "09"]
        prefix = random.choice(prefixes)
        return self.fake.numerify(prefix + "########")

    def _generate_phone_num(self) -> str:
        """Generic VN phone number for PII injection in remarks."""
        return self._generate_emergency_phone()

    def _generate_email(self) -> str:
        return self.fake.email()

    def _generate_national_id(self) -> str:
        return self.fake.numerify("0###########")

    # ------------------------------------------------------------------ #
    # Remarks (template-based, from DB)
    # ------------------------------------------------------------------ #
    def _generate_remarks(self) -> str:
        """Pick a random HR remark template and fill PII if needed."""
        pool = self._load_remarks_pool()
        template = random.choice(pool)
        text = template["template_text"]

        if not template["contain_pii"] or not text:
            return text

        pii_generators = {
            "phone_number": self._generate_phone_num,
            "national_id": self._generate_national_id,
            "email": self._generate_email,
            "bank_account": self._generate_bank_account,
            "tax_id": self._generate_tax_id,
            "emergency_name": self._generate_employee_name,
        }

        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            gen_fn = pii_generators.get(key)
            if gen_fn is None:
                return match.group(0)
            return str(gen_fn())

        return re.sub(r"\$\{(\w+)\}", _replacer, text)

    # ------------------------------------------------------------------ #
    # DB loading (cached)
    # ------------------------------------------------------------------ #
    @classmethod
    def _load_departments_pool(cls) -> list[str]:
        """Fetch departments from Postgres. Cached after first call."""
        if cls._departments_pool is not None:
            return cls._departments_pool

        query = "SELECT department_name FROM public.departments"

        conn = psycopg2.connect(**_DB_CONFIG)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            raise RuntimeError(
                "No data found in public.departments. "
                "Make sure 06_CreateData_HrEmployee.sql has been loaded."
            )

        cls._departments_pool = [r[0] for r in rows]
        return cls._departments_pool

    @classmethod
    def _load_remarks_pool(cls) -> list[dict]:
        """Fetch hr_remarks_templates from Postgres. Cached after first call."""
        if cls._remarks_pool is not None:
            return cls._remarks_pool

        query = """
            SELECT contain_pii, template_text
            FROM public.hr_remarks_templates
        """

        conn = psycopg2.connect(**_DB_CONFIG)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            raise RuntimeError(
                "No data found in public.hr_remarks_templates. "
                "Make sure 06_CreateData_HrEmployee.sql has been loaded."
            )

        cls._remarks_pool = [
            {"contain_pii": r[0], "template_text": r[1]}
            for r in rows
        ]
        return cls._remarks_pool