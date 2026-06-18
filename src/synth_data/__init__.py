"""
synth_data - Synthetic data generation module.

Usage:
    from synth_data import generate

    df = generate("citizen_info", n=100)
    # or
    from synth_data.tables import CitizenInfoGenerator
    gen = CitizenInfoGenerator(seed=42)
    df = gen.generate(n=100)
"""

from synth_data.base import TableGenerator
from synth_data.tables import REGISTRY


def generate(table_name: str, n: int = 100, seed: int | None = None, **kwargs):
    """Generate a DataFrame for the given table name.

    Args:
        table_name: Registered table name (e.g. "citizen_info").
        n: Number of rows.
        seed: Optional seed for reproducibility.
        **kwargs: Extra args forwarded to the generator.

    Returns:
        pandas.DataFrame
    """
    if table_name not in REGISTRY:
        available = ", ".join(sorted(REGISTRY.keys()))
        raise ValueError(
            f"Unknown table '{table_name}'. Available: {available}"
        )

    generator_cls = REGISTRY[table_name]
    generator = generator_cls(seed=seed, **kwargs)
    return generator.generate(n)
