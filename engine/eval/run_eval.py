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
import csv
import json
import sys
from pathlib import Path
from typing import Any

from engine.eval.loader import load_fixtures
from engine.eval.metrics import compute_metrics, format_text_report, metrics_to_json
from engine.eval.runner import run_all_fixtures
from engine.ingest.ingest_v1 import decode_input_path_v1


def _summarize_results(
    results: list[Any],
    *,
    limit_failures: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    counts_by_exc_type: dict[str, int] = {}
    counts_by_engine_error_code: dict[str, int] = {}
    counts_by_stage: dict[str, int] = {}
    counts_by_skip_reason_code: dict[str, int] = {}

    for r in results:
        if getattr(r, "skipped", False):
            code = getattr(r, "skip_reason_code", None) or "unknown"
            counts_by_skip_reason_code[code] = counts_by_skip_reason_code.get(code, 0) + 1
            skipped.append(
                {
                    "path": r.fixture.path,
                    "reason_code": code,
                    "reason": getattr(r, "skip_reason", None),
                }
            )
            continue

        if getattr(r, "success", False):
            continue

        failure = getattr(r, "failure", None) or {}
        exc_type = failure.get("exc_type") or "unknown"
        stage = failure.get("stage") or "unknown"
        engine_error_code = failure.get("engine_error_code") or "unknown"

        counts_by_exc_type[exc_type] = counts_by_exc_type.get(exc_type, 0) + 1
        counts_by_stage[stage] = counts_by_stage.get(stage, 0) + 1
        if engine_error_code != "unknown":
            counts_by_engine_error_code[engine_error_code] = (
                counts_by_engine_error_code.get(engine_error_code, 0) + 1
            )

        failures.append(
            {
                "path": r.fixture.path,
                "stage": stage,
                "exc_type": exc_type,
                "message": failure.get("message") or getattr(r, "error", None),
                "engine_error_code": failure.get("engine_error_code"),
                "traceback_short": failure.get("traceback_short"),
                "traceback_full": failure.get("traceback_full"),
            }
        )

    failures.sort(key=lambda x: x["path"])
    skipped.sort(key=lambda x: x["path"])

    summary_counts: dict[str, Any] = {
        "by_exception_type": dict(
            sorted(counts_by_exc_type.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "by_engine_error_code": dict(
            sorted(counts_by_engine_error_code.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "by_stage": dict(sorted(counts_by_stage.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_skip_reason_code": dict(
            sorted(counts_by_skip_reason_code.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
    }

    if limit_failures >= 0:
        failures = failures[:limit_failures]

    return failures, skipped, summary_counts


def _print_failures_table(failures: list[dict[str, Any]]) -> None:
    if not failures:
        return

    print("\nFailures:", file=sys.stderr)
    print("path\tstage\tengine_error_code\texc_type\tmessage", file=sys.stderr)
    for f in failures:
        msg = (f.get("message") or "").replace("\n", " ")
        print(
            f"{f.get('path', '')}\t{f.get('stage', '')}\t{f.get('engine_error_code', '')}\t"
            f"{f.get('exc_type', '')}\t{msg}",
            file=sys.stderr,
        )


def _percentile_linear(sorted_vals: list[float], p: float) -> float:
    """
    Deterministic percentile with linear interpolation.
    - `sorted_vals` must be non-empty and sorted ascending.
    - `p` in [0, 1]
    """
    if not sorted_vals:
        raise ValueError("sorted_vals must be non-empty")
    if p <= 0.0:
        return float(sorted_vals[0])
    if p >= 1.0:
        return float(sorted_vals[-1])

    n = len(sorted_vals)
    pos = p * float(n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    if hi == lo:
        return float(sorted_vals[lo])
    frac = pos - float(lo)
    return float(sorted_vals[lo]) + frac * (float(sorted_vals[hi]) - float(sorted_vals[lo]))


def _bpm_hint_windows_summary(
    bpm_hint_windows: list[float] | None,
    *,
    top1_bpm: float | None,
    tol_bpm: float = 1.0,
) -> dict[str, Any]:
    hints = [float(x) for x in (bpm_hint_windows or []) if x is not None]
    if not hints:
        return {
            "count": 0,
            "median": None,
            "iqr": None,
            "pct_within_1_top1": None,
            "pct_within_1_double_top1": None,
        }

    hints.sort()
    med = _percentile_linear(hints, 0.5)
    q1 = _percentile_linear(hints, 0.25)
    q3 = _percentile_linear(hints, 0.75)
    iqr = q3 - q1

    pct_top1 = None
    pct_double = None
    if top1_bpm is not None:
        t = float(top1_bpm)
        within_top1 = sum(1 for x in hints if abs(float(x) - t) <= float(tol_bpm))
        within_double = sum(1 for x in hints if abs(float(x) - (2.0 * t)) <= float(tol_bpm))
        pct_top1 = within_top1 / float(len(hints))
        pct_double = within_double / float(len(hints))

    return {
        "count": int(len(hints)),
        "median": float(med),
        "iqr": float(iqr),
        "pct_within_1_top1": pct_top1,
        "pct_within_1_double_top1": pct_double,
    }


def _extract_bpm_confidence(output: dict[str, Any] | None) -> Any:
    """
    Best-effort extraction of confidence from packaged output.
    Keeps DO-NOT-LIE: if not present, returns None.
    """
    if not output:
        return None
    m = output.get("metrics")
    if not isinstance(m, dict):
        return None
    bpm = m.get("bpm")
    if not isinstance(bpm, dict):
        return None

    v = bpm.get("value")
    if isinstance(v, dict) and "confidence" in v:
        return v.get("confidence")
    if "confidence" in bpm:
        return bpm.get("confidence")
    return None


def _fixture_debug_rows(results: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in results:
        fixture = r.fixture
        output = getattr(r, "output", None)
        bpm_block: dict[str, Any] | None = None
        try:
            if isinstance(output, dict):
                m = output.get("metrics")
                if isinstance(m, dict) and isinstance(m.get("bpm"), dict):
                    bpm_block = m.get("bpm")  # type: ignore[assignment]
        except Exception:
            bpm_block = None

        # Candidates (top 5 rounded values)
        top_candidates: list[int] = []
        for c in getattr(r, "bpm_candidates", None) or []:
            val = c.get("value", {})
            if isinstance(val, dict):
                vr = val.get("value_rounded")
                if vr is not None:
                    top_candidates.append(int(vr))
            elif isinstance(val, (int, float)):
                top_candidates.append(int(round(val)))
            if len(top_candidates) >= 5:
                break

        top1 = float(top_candidates[0]) if top_candidates else None

        # Hint windows summary: recompute from ingest for deterministic debug export.
        bpm_hint_windows: list[float] | None = None
        if not getattr(r, "skipped", False):
            try:
                audio = decode_input_path_v1(Path(fixture.path))
                bpm_hint_windows = getattr(audio, "bpm_hint_windows", None)
            except Exception:
                bpm_hint_windows = None

        hint_summary = _bpm_hint_windows_summary(bpm_hint_windows, top1_bpm=top1, tol_bpm=1.0)

        confidence = _extract_bpm_confidence(output)
        omitted = bool(getattr(r, "bpm_omitted", False))
        if not omitted:
            omitted_due_to_confidence: bool | None = False
        else:
            # Only assert True when we have explicit label evidence.
            omitted_due_to_confidence = True if str(confidence).lower() == "low" else None

        predicted_bpm_raw = None
        predicted_bpm_raw_confidence = None
        predicted_bpm_reportable = None
        predicted_bpm_reportable_confidence = None
        predicted_timefeel = None
        predicted_reason_codes = None
        if bpm_block is not None:
            predicted_bpm_raw = bpm_block.get("bpm_raw")
            predicted_bpm_raw_confidence = bpm_block.get("bpm_raw_confidence")
            predicted_bpm_reportable = bpm_block.get("bpm_reportable")
            predicted_bpm_reportable_confidence = bpm_block.get("bpm_reportable_confidence")
            predicted_timefeel = bpm_block.get("timefeel")
            predicted_reason_codes = bpm_block.get("bpm_reason_codes")

        rows.append(
            {
                "path": fixture.path,
                "bpm_gt_raw": getattr(fixture, "bpm_gt_raw", None),
                "bpm_gt_reportable": getattr(fixture, "bpm_gt_reportable", None),
                "predicted_bpm_value_rounded": getattr(r, "bpm_value_rounded", None),
                "predicted_bpm_confidence": confidence,
                "predicted_bpm_raw": predicted_bpm_raw,
                "predicted_bpm_raw_confidence": predicted_bpm_raw_confidence,
                "predicted_bpm_reportable": predicted_bpm_reportable,
                "predicted_bpm_reportable_confidence": predicted_bpm_reportable_confidence,
                "predicted_timefeel": predicted_timefeel,
                "predicted_bpm_reason_codes": predicted_reason_codes,
                "top_candidates_rounded": top_candidates,
                "bpm_omitted": omitted,
                "omitted_due_to_confidence": omitted_due_to_confidence,
                "bpm_hint_windows_summary": hint_summary,
            }
        )

    rows.sort(key=lambda x: x["path"])
    return rows


def _dump_fixture_debug_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "path",
        "bpm_gt_raw",
        "bpm_gt_reportable",
        "predicted_bpm_value_rounded",
        "predicted_bpm_confidence",
        "bpm_omitted",
        "omitted_due_to_confidence",
        "top_candidates_rounded",
        "bpm_hint_windows_count",
        "bpm_hint_windows_median",
        "bpm_hint_windows_iqr",
        "bpm_hint_windows_pct_within_1_top1",
        "bpm_hint_windows_pct_within_1_double_top1",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            hs = r.get("bpm_hint_windows_summary") or {}
            w.writerow(
                {
                    "path": r.get("path"),
                    "bpm_gt_raw": r.get("bpm_gt_raw"),
                    "bpm_gt_reportable": r.get("bpm_gt_reportable"),
                    "predicted_bpm_value_rounded": r.get("predicted_bpm_value_rounded"),
                    "predicted_bpm_confidence": r.get("predicted_bpm_confidence"),
                    "bpm_omitted": r.get("bpm_omitted"),
                    "omitted_due_to_confidence": r.get("omitted_due_to_confidence"),
                    "top_candidates_rounded": json.dumps(r.get("top_candidates_rounded") or []),
                    "bpm_hint_windows_count": hs.get("count"),
                    "bpm_hint_windows_median": hs.get("median"),
                    "bpm_hint_windows_iqr": hs.get("iqr"),
                    "bpm_hint_windows_pct_within_1_top1": hs.get("pct_within_1_top1"),
                    "bpm_hint_windows_pct_within_1_double_top1": hs.get("pct_within_1_double_top1"),
                }
            )


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
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failure (default: process all fixtures)",
    )
    parser.add_argument(
        "--print-failures",
        action="store_true",
        help="Print a TSV table of failures to stderr (default: off)",
    )
    parser.add_argument(
        "--debug-traceback",
        action="store_true",
        help="Include full tracebacks in JSON report (default: short tracebacks only)",
    )
    parser.add_argument(
        "--limit-failures",
        type=int,
        default=20,
        help="Max failures to include in JSON report (default: 20; -1 for unlimited)",
    )
    parser.add_argument(
        "--dump-fixtures-csv",
        type=Path,
        help="Optional: write per-fixture debug summary CSV to this path",
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
            fail_fast=args.fail_fast,
            debug_traceback=args.debug_traceback,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Compute metrics
    metrics = compute_metrics(results, top_n_errors=args.top_n)

    # Print text report to stderr
    text_report = format_text_report(metrics)
    print("\n" + text_report, file=sys.stderr)

    failures, skipped, summary_counts = _summarize_results(
        results,
        limit_failures=args.limit_failures,
    )

    fixture_rows = _fixture_debug_rows(results)
    if args.dump_fixtures_csv:
        _dump_fixture_debug_csv(args.dump_fixtures_csv, fixture_rows)

    if args.print_failures:
        _print_failures_table(failures)

    # Output JSON
    json_report = metrics_to_json(metrics)
    json_report["failures"] = failures
    json_report["skipped"] = skipped
    json_report["summary_counts"] = summary_counts
    json_report["fixtures"] = fixture_rows
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
