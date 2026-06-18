"""
Table generator registry.

To add a new table:
    1. Create a new module in ``synth_data/tables/`` (e.g. ``my_table.py``).
    2. Subclass ``TableGenerator`` and implement the required members.
    3. Import the class here and add it to ``REGISTRY``.
"""

from synth_data.tables.citizen_info import CitizenInfoGenerator

# Maps table_name -> generator class.
# Add new entries as you create more tables.
REGISTRY: dict[str, type] = {
    CitizenInfoGenerator.table_name: CitizenInfoGenerator,
}

__all__ = [
    "REGISTRY",
    "CitizenInfoGenerator",
]
