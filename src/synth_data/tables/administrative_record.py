"""
Generator for the administrative record table.
- contains semi-structured data (notes)

Purpose:
    - LLM semantic understanding
    - PII hidden inside free text
"""

import random
import re

import psycopg2

from synth_data.base import TableGenerator
from synth_data.tables.citizen_info import CitizenInfoGenerator
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Reuse CitizenInfoGenerator's PII helpers via composition.
        self._citizen_gen = CitizenInfoGenerator(
            locale=kwargs.get("locale", "vi_VN"),
            seed=kwargs.get("seed"),
        )

    # ------------------------------------------------------------------ #
    # Row generation
    # ------------------------------------------------------------------ #
    def _generate_row(self, index: int) -> dict:
        template = self._pick_template()

        return {
            "record_id": index + 1,
            "service_type": template["service_name_vn"],
            "applicant_name": self._citizen_gen.generate_full_name(),
            "cccd_number": self._citizen_gen.generate_national_id(),
            "submission_date": self.fake.date_between(
                start_date="-2y", end_date="today"
            ).isoformat(),
            "status": template["status_en"],
            "clerk_notes": self._render_clerk_note(template),
        }

    # ------------------------------------------------------------------ #
    # Template handling
    # ------------------------------------------------------------------ #
    def _pick_template(self) -> dict:
        """Return a random template dict from the cached pool."""
        pool = self._load_templates_pool()
        return random.choice(pool)

    def _render_clerk_note(self, template: dict) -> str:
        """Replace PII placeholders in the clerk note if contain_pii is True."""
        note = template["clerk_note"]

        if not template["contain_pii"]:
            return note

        # Map each placeholder to a generator method.
        pii_generators = {
            "phone_number": self._citizen_gen.generate_phone_num,
            "national_id": self._citizen_gen.generate_national_id,
            "full_name": self._citizen_gen.generate_full_name,
            "email": self._citizen_gen.generate_email,
            "bank_account": self._generate_bank_account,
        }

        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            gen_fn = pii_generators.get(key)
            if gen_fn is None:
                return match.group(0)  # leave unknown placeholders as-is
            return str(gen_fn())

        return re.sub(r"\$\{(\w+)\}", _replacer, note)

    # ------------------------------------------------------------------ #
    # Extra PII generators (not in CitizenInfoGenerator)
    # ------------------------------------------------------------------ #
    def _generate_bank_account(self) -> str:
        """Produce a fake Vietnamese bank account number (10-14 digits)."""
        length = random.choice([10, 12, 13, 14])
        return self.fake.numerify("#" * length)

    # ------------------------------------------------------------------ #
    # DB loading (cached)
    # ------------------------------------------------------------------ #
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