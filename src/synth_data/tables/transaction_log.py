"""
Generator for the transaction logs table.
- contains pii data in finance
- contains semi-structured data (notes)
- contains columns with potential sensitive data
    + transaction note: free text data, may or may not contain senstive data
    + fraud_note: free text data, may or may not contain sensitive data, contains mostly null values

Purpose:
    - LLM semantic understanding
    - PII hidden inside free text
    - Handle potential sensitive columns with large amount of NULL values
"""

import random
import re
from datetime import datetime, timedelta

import psycopg2

from synth_data.base import TableGenerator
from synth_data.tables.settings import _DB_CONFIG

# Probability that fraud_notes is NOT null (< 1%).
_FRAUD_NOTE_PROBABILITY = 0.008


class TransactionLogGenerator(TableGenerator):
    """Generates synthetic banking transaction log records.

    - ``tx_message`` is drawn from ``tx_message_templates`` in Postgres.
    - ``fraud_notes`` is drawn from ``fraud_note_templates`` but is NULL
      for >99 % of rows.
    - PII placeholders (``${phone_number}``, ``${tax_id}``, …) are
      replaced with fake data when the template's ``contain_pii`` flag
      is True.
    """

    table_name = "transaction_log"
    columns = [
        "tx_id",
        "tx_timestamp",
        "tx_type",
        "amount",
        "source_account",
        "target_account",
        "tax_id",
        "customer_name",
        "tx_message",
        "fraud_notes",
    ]

    # Cached DB data — loaded once across all instances.
    _tx_types_pool: list[str] | None = None
    _tx_msg_pool: list[dict] | None = None
    _fraud_note_pool: list[dict] | None = None

    # ------------------------------------------------------------------ #
    # Row generation
    # ------------------------------------------------------------------ #
    def _generate_row(self, index: int) -> dict:
        tx_msg_template = self._pick_tx_message_template()
        fraud_template = self._pick_fraud_note_template()

        return {
            "tx_id": index + 1,
            "tx_timestamp": self._generate_tx_timestamp(),
            "tx_type": self._generate_tx_type(),
            "amount": self._generate_amount(),
            "source_account": self._generate_bank_account(),
            "target_account": self._generate_bank_account(),
            "tax_id": self._generate_tax_id(),
            "customer_name": self._generate_full_name(),
            "tx_message": self._generate_tx_message(tx_msg_template),
            "fraud_notes": self._generate_fraud_notes(fraud_template),
        }

    # ------------------------------------------------------------------ #
    # Column generators
    # ------------------------------------------------------------------ #
    def _generate_tx_timestamp(self) -> str:
        """Random timestamp within the last 2 years."""
        start = datetime.now() - timedelta(days=730)
        random_dt = self.fake.date_time_between(
            start_date=start, end_date="now"
        )
        return random_dt.strftime("%Y-%m-%d %H:%M:%S")

    def _generate_tx_type(self) -> str:
        pool = self._load_tx_types_pool()
        return random.choice(pool)

    def _generate_amount(self) -> float:
        """Random amount between 10,000 and 500,000,000 VND, rounded."""
        return round(random.uniform(10_000, 500_000_000), -3)

    def _generate_bank_account(self) -> str:
        """Produce a fake Vietnamese bank account number (10-14 digits)."""
        length = random.choice([10, 12, 13, 14])
        return self.fake.numerify("#" * length)

    def _generate_tax_id(self) -> str:
        """Produce a fake Vietnamese tax ID (Mã số thuế).
        Format: 10 or 13 digits."""
        if random.random() < 0.7:
            return self.fake.numerify("##########")      # 10-digit personal
        return self.fake.numerify("#########-###")        # 13-digit branch

    def _generate_full_name(self) -> str:
        return self.fake.name()

    def _generate_phone_num(self) -> str:
        prefixes = ["03", "05", "07", "08", "09"]
        prefix = random.choice(prefixes)
        return self.fake.numerify(prefix + "########")

    def _generate_email(self) -> str:
        return self.fake.email()

    def _generate_national_id(self) -> str:
        return self.fake.numerify("0###########")

    # ------------------------------------------------------------------ #
    # Template-based text fields
    # ------------------------------------------------------------------ #
    def _generate_tx_message(self, template: dict) -> str:
        """Render a tx_message template, replacing PII placeholders."""
        return self._render_template(template)

    def _generate_fraud_notes(self, template: dict | None) -> str | None:
        """Render a fraud_note template if selected (>99% chance of NULL)."""
        if template is None:
            return None
        return self._render_template(template)

    def _render_template(self, template: dict) -> str:
        """Replace ``${...}`` PII placeholders with generated fake data."""
        text = template["template_text"]

        if not template["contain_pii"]:
            return text

        pii_generators = {
            "phone_number": self._generate_phone_num,
            "national_id": self._generate_national_id,
            "full_name": self._generate_full_name,
            "email": self._generate_email,
            "bank_account": self._generate_bank_account,
            "tax_id": self._generate_tax_id,
        }

        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            gen_fn = pii_generators.get(key)
            if gen_fn is None:
                return match.group(0)
            return str(gen_fn())

        return re.sub(r"\$\{(\w+)\}", _replacer, text)

    # ------------------------------------------------------------------ #
    # Template pickers
    # ------------------------------------------------------------------ #
    def _pick_tx_message_template(self) -> dict:
        pool = self._load_tx_msg_pool()
        return random.choice(pool)

    def _pick_fraud_note_template(self) -> dict | None:
        """Return a fraud note template with <1% probability, else None."""
        if random.random() > _FRAUD_NOTE_PROBABILITY:
            return None
        pool = self._load_fraud_note_pool()
        return random.choice(pool)

    # ------------------------------------------------------------------ #
    # DB loading (cached)
    # ------------------------------------------------------------------ #
    @classmethod
    def _load_tx_types_pool(cls) -> list[str]:
        """Fetch tx_types from Postgres. Cached after first call."""
        if cls._tx_types_pool is not None:
            return cls._tx_types_pool

        query = "SELECT type_code FROM public.tx_types"

        conn = psycopg2.connect(**_DB_CONFIG)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            raise RuntimeError(
                "No data found in public.tx_types. "
                "Make sure 05_CreateData_TxLogs.sql has been loaded."
            )

        cls._tx_types_pool = [r[0] for r in rows]
        return cls._tx_types_pool

    @classmethod
    def _load_tx_msg_pool(cls) -> list[dict]:
        """Fetch tx_message_templates from Postgres. Cached after first call."""
        if cls._tx_msg_pool is not None:
            return cls._tx_msg_pool

        query = """
            SELECT contain_pii, template_text
            FROM public.tx_message_templates
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
                "No data found in public.tx_message_templates. "
                "Make sure 05_CreateData_TxLogs.sql has been loaded."
            )

        cls._tx_msg_pool = [
            {"contain_pii": r[0], "template_text": r[1]}
            for r in rows
        ]
        return cls._tx_msg_pool

    @classmethod
    def _load_fraud_note_pool(cls) -> list[dict]:
        """Fetch fraud_note_templates from Postgres. Cached after first call."""
        if cls._fraud_note_pool is not None:
            return cls._fraud_note_pool

        query = """
            SELECT contain_pii, template_text
            FROM public.fraud_note_templates
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
                "No data found in public.fraud_note_templates. "
                "Make sure 05_CreateData_TxLogs.sql has been loaded."
            )

        cls._fraud_note_pool = [
            {"contain_pii": r[0], "template_text": r[1]}
            for r in rows
        ]
        return cls._fraud_note_pool