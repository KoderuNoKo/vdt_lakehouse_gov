"""Generator for the citizen_info table."""

from synth_data.base import TableGenerator


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

    def _generate_row(self, index: int) -> dict:
        return {
            "citizen_id": index + 1,
            "full_name": self.fake.name(),
            "national_id": self.fake.numerify("0#########"),  # 10-digit ID
            "phone_number": self.fake.numerify("09########"),  # VN mobile format
            "email": self.fake.email(),
            "birth_date": self.fake.date_of_birth(
                minimum_age=18, maximum_age=80
            ).isoformat(),
            "address": self.fake.address(),
            "occupation": self.fake.job(),
        }
