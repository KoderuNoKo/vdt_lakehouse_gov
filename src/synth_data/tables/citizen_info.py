"""
Generator for the citizen_info table.
- Obvious PII fields

Purpose:
    - Easy for regex
    - Easy for LLM
    - Baseline evaluation
"""

import random

import psycopg2

from synth_data.base import TableGenerator
from synth_data.tables.settings import _DB_CONFIG


class CitizenInfoGenerator(TableGenerator):
    """Generates synthetic Vietnamese citizen information."""

    table_name = "citizen_info"
    columns = [
        "citizen_id",
        "full_name",
        "national_id",
        "phone_number",
        "email",
        "birth_date",
        "address",
        "occupation",
    ]

    # Shared across instances — loaded once.
    _address_pool: list[tuple[str, str]] | None = None

    def _generate_row(self, index: int) -> dict:
        return {
            "citizen_id": index + 1,
            "full_name": self.generate_full_name(),
            "national_id": self.generate_national_id(),  
            "phone_number": self.generate_phone_num(),
            "email": self.generate_email(),
            "birth_date": self.generate_dob(minimum_age=18, maximum_age=100),
            "address": self.generate_address(),
            "occupation": self.generate_job(),
        }

    def generate_full_name(self):
        """produce a fake full name using Faker"""
        return self.fake.name()

    def generate_national_id(self):
        """produce a 12-digits cccd number starting with 0"""
        return self.fake.numerify("0###########")

    def generate_phone_num(self) -> int:
        """produce a vn phone num format, 2 valid prefix digits and 8 random digits"""
        prefixes = ['03', '05', '07', '08', '09']
        prefix = random.choice(prefixes)
        return self.fake.numerify(prefix + "########")
    
    def generate_email(self):
        """produce a fake email using Faker"""
        return self.fake.email()

    def generate_dob(self, minimum_age, maximum_age):
        """produce a fake date of birth using Faker"""
        return self.fake.date_of_birth(minimum_age=minimum_age, maximum_age=maximum_age).isoformat()

    def generate_address(self) -> str:
        """Build a realistic Vietnamese address.

        Format: ``<house_number> <street>, <ward>, <province>``
        Ward and province are real values pulled from the DB.
        """
        pool = self._load_address_pool()
        ward_name, province_name = random.choice(pool)

        house_number = random.randint(1, 999)
        street = self.fake.street_name()

        return f"{house_number} {street}, {ward_name}, {province_name}"

    def generate_job(self):
        return self.fake.job()

    @classmethod
    def _load_address_pool(cls) -> list[tuple[str, str]]:
        """Fetch all ward-province pairs from the Postgres DB (once)."""
        query = """
            SELECT w.full_name  AS ward_name,
            p.full_name  AS province_name
            FROM public.wards w
            JOIN public.provinces p ON w.province_code = p.code
        """
        if cls._address_pool is not None:
            return cls._address_pool

        conn = psycopg2.connect(**_DB_CONFIG)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                cls._address_pool = cur.fetchall()
        finally:
            conn.close()

        if not cls._address_pool:
            raise RuntimeError(
                "No address data found in public.wards / public.provinces. "
                "Make sure the Vietnamese provinces dataset is loaded."
            )
        return cls._address_pool