"""
Table generator registry.

To add a new table:
    1. Create a new module in ``synth_data/tables/`` (e.g. ``my_table.py``).
    2. Subclass ``TableGenerator`` and implement the required members.
    3. Import the class here and add it to ``REGISTRY``.
"""

from synth_data.tables.citizen_info import CitizenInfoGenerator
from synth_data.tables.administrative_record import AdministrativeRecordGenerator
from synth_data.tables.transaction_log import TransactionLogGenerator
from synth_data.tables.hr_employee_ambiguous import HrEmployeeAmbiguousGenerator

# Maps table_name -> generator class.
# Add new entries as you create more tables.
REGISTRY: dict[str, type] = {
    CitizenInfoGenerator.table_name: CitizenInfoGenerator,
    AdministrativeRecordGenerator.table_name: AdministrativeRecordGenerator,
    TransactionLogGenerator.table_name: TransactionLogGenerator,
    HrEmployeeAmbiguousGenerator.table_name: HrEmployeeAmbiguousGenerator,
}

__all__ = [
    "REGISTRY",
    "CitizenInfoGenerator",
    "AdministrativeRecordGenerator",
    "TransactionLogGenerator",
    "HrEmployeeAmbiguousGenerator",
]
