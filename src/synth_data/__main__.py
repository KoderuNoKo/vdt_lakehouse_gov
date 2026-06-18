"""CLI entry point: ``python -m synth_data``."""

import argparse
import sys

# Ensure Vietnamese characters print correctly on Windows consoles.
sys.stdout.reconfigure(encoding="utf-8")

from synth_data import generate
from synth_data.tables import REGISTRY


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic data tables."
    )
    parser.add_argument(
        "table",
        choices=sorted(REGISTRY.keys()),
        help="Table to generate.",
    )
    parser.add_argument(
        "-n", "--rows",
        type=int,
        default=10,
        help="Number of rows (default: 10).",
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (.csv or .parquet). Prints to stdout if omitted.",
    )

    args = parser.parse_args()
    df = generate(args.table, n=args.rows, seed=args.seed)

    if args.output is None:
        print(df.to_string(index=False))
    elif args.output.endswith(".parquet"):
        df.to_parquet(args.output, index=False)
        print(f"Wrote {len(df)} rows to {args.output}")
    else:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
