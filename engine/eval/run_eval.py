#!/usr/bin/env python3
"""
Evaluation harness CLI for BeetsNKeys analysis engine v1.

Usage:
    PYTHONPATH=. python3 engine/eval/run_eval.py [OPTIONS]

Examples:
    # Run with defaults (fixtures.csv, role=pro)
    PYTHONPATH=. python3 engine/eval/run_eval.py

    # Custom fixtures and output
    PYTHONPATH=. python3 engine/eval/run_eval.py --fixtures my_fixtures.csv --output results.json

    # Limit to first 5 fixtures
    PYTHONPATH=. python3 engine/eval/run_eval.py --limit 5

    # Fail if any audio file is missing
    PYTHONPATH=. python3 engine/eval/run_eval.py --fail-on-missing-files
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.eval.loader import load_fixtures
from engine.eval.metrics import compute_metrics, format_text_report, metrics_to_json
from engine.eval.runner import run_all_fixtures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run evaluation on BeetsNKeys analysis engine v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("engine/eval/fixtures.csv"),
        help="Path to fixtures CSV (default: engine/eval/fixtures.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to save JSON report (default: print to stdout)",
    )
    parser.add_argument(
        "--role",
        type=str,
        default="pro",
        choices=["guest", "free", "pro"],
        help="Analysis role (default: pro)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of fixtures to process",
    )
    parser.add_argument(
        "--fail-on-missing-files",
        action="store_true",
        help="Error if any fixture audio file is missing (default: skip and record)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of worst BPM errors to report (default: 20)",
    )

    args = parser.parse_args()

    # Load fixtures
    print(f"Loading fixtures from: {args.fixtures}", file=sys.stderr)
    try:
        fixtures = load_fixtures(args.fixtures)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading fixtures: {exc}", file=sys.stderr)
        return 1

    if not fixtures:
        print(
            "No fixtures found in CSV (all rows were comments or empty).",
            file=sys.stderr,
        )
        return 1

    print(f"Loaded {len(fixtures)} fixture(s)", file=sys.stderr)

    # Apply limit
    if args.limit:
        fixtures = fixtures[: args.limit]
        print(f"Limited to {len(fixtures)} fixture(s)", file=sys.stderr)

    # Run evaluation
    print(f"Running analysis with role={args.role}...", file=sys.stderr)
    try:
        results = run_all_fixtures(
            fixtures,
            role=args.role,
            fail_on_missing=args.fail_on_missing_files,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Compute metrics
    metrics = compute_metrics(results, top_n_errors=args.top_n)

    # Print text report to stderr
    text_report = format_text_report(metrics)
    print("\n" + text_report, file=sys.stderr)

    # Output JSON
    json_report = metrics_to_json(metrics)
    json_str = json.dumps(json_report, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"\nJSON report saved to: {args.output}", file=sys.stderr)
    else:
        # Print JSON to stdout (can be piped)
        print(json_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
