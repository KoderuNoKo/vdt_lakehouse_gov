"""
Generator for the administrative record table.
- contains semi-structured data (notes): may or may not contain sensitive data

Purpose:
    - LLM semantic understanding
    - PII hidden inside free text
"""

import random
import re

import psycopg2

from synth_data.base import TableGenerator
from synth_data.tables.settings import _DB_CONFIG


class AdministrativeRecordGenerator(TableGenerator):
    """Generates synthetic administrative process records.

    Clerk notes are pulled from DB templates and PII placeholders
    (${phone_number}, ${national_id}, etc.) are filled with fake data
    when the template's ``contain_pii`` flag is True.
    """

    table_name = "administrative_record"
    columns = [
        "record_id",
        "service_type",
        "applicant_name",
        "cccd_number",
        "submission_date",
        "status",
        "clerk_notes",
    ]

    # Cached DB data — loaded once across all instances.
    _templates_pool: list[dict] | None = None

    def _generate_row(self, index: int) -> dict:
        template = self._pick_clerk_note_template()
        return {
            "record_id": index + 1,
            "service_type": self._generate_service_type(template),
            "applicant_name": self._generate_full_name(),
            "cccd_number": self._generate_national_id(),
            "submission_date": self._generate_submission_date(),
            "status": self._generate_status(template),
            "clerk_notes": self._generate_clerk_note(template),
        }

    def _generate_service_type(self, template: dict) -> str:
        return template["service_name_vn"]
    
    def _generate_full_name(self) -> str:
        """produce a fake full name using Faker"""
        return self.fake.name()

    def _generate_national_id(self) -> str:
        """produce a 12-digits cccd number starting with 0"""
        return self.fake.numerify("0###########")

    def _generate_submission_date(self) -> str:
        return self.fake.date_between(
            start_date="-2y", end_date="today"
        ).isoformat()

    def _generate_status(self, template: dict) -> str:
        return template["status_en"]

    def _generate_phone_num(self) -> str:
        """produce a vn phone num format, 2 valid prefix digits and 8 random digits"""
        prefixes = ['03', '05', '07', '08', '09']
        prefix = random.choice(prefixes)
        return self.fake.numerify(prefix + "########")
    
    def _generate_email(self) -> str:
        """produce a fake email using Faker"""
        return self.fake.email()

    def _generate_clerk_note(self, template: dict) -> str:
        """Replace PII placeholders in the clerk note if contain_pii is True."""
        note = template["clerk_note"]

        if not template["contain_pii"]:
            return note

        # Map each placeholder to a generator method.
        pii_generators = {
            "phone_number": self._generate_phone_num,
            "national_id": self._generate_national_id,
            "full_name": self._generate_full_name,
            "email": self._generate_email,
            "bank_account": self._generate_bank_account,
        }

        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            gen_fn = pii_generators.get(key)
            if gen_fn is None:
                return match.group(0)  # leave unknown placeholders as-is
            return str(gen_fn())

        return re.sub(r"\$\{(\w+)\}", _replacer, note)

    def _generate_bank_account(self) -> str:
        """Produce a fake Vietnamese bank account number (10-14 digits)."""
        length = random.choice([10, 12, 13, 14])
        return self.fake.numerify("#" * length)

    @classmethod
    def _load_templates_pool(cls) -> list[dict]:
        """Fetch clerk_notes_templates joined with service_types and
        record_statuses from the Postgres DB. Cached after first call."""
        if cls._templates_pool is not None:
            return cls._templates_pool

        query = """
            SELECT
                st.service_name_vn,
                rs.status_en,
                cn.contain_pii,
                cn.clerk_note
            FROM public.clerk_notes_templates cn
            JOIN public.service_types   st ON cn.service_type_id = st.id
            JOIN public.record_statuses rs ON cn.status_id       = rs.id
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
                "No data found in public.clerk_notes_templates. "
                "Make sure 04_CreateData_AdministrativeRecord.sql has been loaded."
            )

        cls._templates_pool = [
            {
                "service_name_vn": r[0],
                "status_en": r[1],
                "contain_pii": r[2],
                "clerk_note": r[3],
            }
            for r in rows
        ]
        return cls._templates_pool
    
    def _pick_clerk_note_template(self) -> dict:
        """Return a random template dict from the cached pool."""
        pool = self._load_templates_pool()
        return random.choice(pool)