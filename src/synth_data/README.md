# synth_data

Synthetic data generation module.
Generates realistic Vietnamese-locale fake data using **Faker** and **pandas**.

## Structure

```
synth_data/
├── __init__.py        # Package API — generate()
├── __main__.py        # CLI entry point
├── base.py            # Abstract TableGenerator base class
└── tables/
    ├── __init__.py    # Table registry (REGISTRY)
    └── citizen_info.py
```

## Quick Start

### Python API

```python
from synth_data import generate

df = generate("citizen_info", n=1000, seed=42)
```

### CLI

```bash
# Print to stdout
python -m synth_data citizen_info -n 10

# Export to file
python -m synth_data citizen_info -n 1000 -o output.csv
python -m synth_data citizen_info -n 1000 -o output.parquet

# Reproducible output
python -m synth_data citizen_info -n 500 -s 42
```

## Adding a New Table

1. **Create** `tables/my_table.py`:

```python
from synth_data.base import TableGenerator

class MyTableGenerator(TableGenerator):
    table_name = "my_table"
    columns = ["id", "col_a", "col_b"]

    def _generate_row(self, index: int) -> dict:
        return {
            "id": index + 1,
            "col_a": self.fake.name(),
            "col_b": self.fake.date(),
        }
```

2. **Register** in `tables/__init__.py`:

```python
from synth_data.tables.my_table import MyTableGenerator

REGISTRY: dict[str, type] = {
    # ... existing entries ...
    MyTableGenerator.table_name: MyTableGenerator,
}
```

3. **Use** it immediately:

```python
generate("my_table", n=100)
```

## Dependencies

- `faker`
- `pandas`
