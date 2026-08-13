"""Command-line entry point for reproducible anomaly evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sentinel behavioral anomaly evaluation.")
    parser.add_argument("fixture", type=Path, help="Path to a labeled JSONL fixture")
    parser.add_argument(
        "--training-count",
        type=int,
        default=2,
        help="Number of initial samples used for training (default: 2)",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report output path")
    args = parser.parse_args()
    report = run_fixture(args.fixture, training_count=args.training_count)
    rendered = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
