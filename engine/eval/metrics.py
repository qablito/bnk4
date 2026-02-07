"""Compute evaluation metrics."""

from __future__ import annotations

from typing import Any

from engine.eval.eval_types import BpmError, EvalMetrics, PredictionResult


def compute_metrics(
    results: list[PredictionResult],
    *,
    top_n_errors: int = 20,
) -> EvalMetrics:
    """
    Compute evaluation metrics from prediction results.

    Args:
        results: List of prediction results.
        top_n_errors: Number of worst BPM errors to include.

    Returns:
        EvalMetrics with computed metrics.
    """
    total = len(results)
    successful = sum(1 for r in results if r.success and not r.skipped)
    failed = sum(1 for r in results if not r.success and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)

    # BPM metrics (only bpm_strict fixtures that ran successfully)
    bpm_strict_results = [
        r for r in results if r.success and not r.skipped and r.fixture.is_bpm_strict
    ]
    bpm_n_total_strict = len(bpm_strict_results)

    # Predicted = not omitted
    bpm_predicted_results = [r for r in bpm_strict_results if not r.bpm_omitted]
    bpm_n_predicted = len(bpm_predicted_results)
    bpm_n_omitted = bpm_n_total_strict - bpm_n_predicted

    # Compute MAE and collect errors
    bpm_mae = None
    bpm_omit_rate = None
    bpm_errors_list: list[BpmError] = []

    if bpm_n_total_strict > 0:
        bpm_omit_rate = bpm_n_omitted / bpm_n_total_strict

    if bpm_predicted_results:
        abs_errors = []
        for r in bpm_predicted_results:
            if r.fixture.bpm_gt is not None and r.bpm_value_rounded is not None:
                abs_error = abs(r.bpm_value_rounded - r.fixture.bpm_gt)
                abs_errors.append(abs_error)

                # Extract candidate values (rounded) for debugging
                candidates_rounded = None
                if r.bpm_candidates:
                    candidates_rounded = []
                    for c in r.bpm_candidates:
                        val = c.get("value", {})
                        if isinstance(val, dict):
                            vr = val.get("value_rounded")
                            if vr is not None:
                                candidates_rounded.append(vr)
                        elif isinstance(val, (int, float)):
                            candidates_rounded.append(int(round(val)))

                bpm_errors_list.append(
                    BpmError(
                        path=r.fixture.path,
                        bpm_gt=r.fixture.bpm_gt,
                        bpm_pred=r.bpm_value_rounded,
                        abs_error=abs_error,
                        candidates=candidates_rounded,
                        notes=r.fixture.notes,
                    )
                )

        if abs_errors:
            bpm_mae = sum(abs_errors) / len(abs_errors)

    # Sort BPM errors by abs_error descending, take top N
    bpm_errors_list.sort(key=lambda e: e.abs_error, reverse=True)
    top_bpm_errors = bpm_errors_list[:top_n_errors]

    return EvalMetrics(
        total_fixtures=total,
        successful_runs=successful,
        failed_runs=failed,
        skipped_runs=skipped,
        bpm_n_total_strict=bpm_n_total_strict,
        bpm_n_predicted=bpm_n_predicted,
        bpm_n_omitted=bpm_n_omitted,
        bpm_mae=bpm_mae,
        bpm_omit_rate=bpm_omit_rate,
        top_bpm_errors=top_bpm_errors,
    )


def metrics_to_json(metrics: EvalMetrics) -> dict[str, Any]:
    """Convert EvalMetrics to a JSON-serializable dict with stable keys."""
    return {
        "overall": {
            "total_fixtures": metrics.total_fixtures,
            "successful_runs": metrics.successful_runs,
            "failed_runs": metrics.failed_runs,
            "skipped_runs": metrics.skipped_runs,
        },
        "bpm": {
            "n_total_strict": metrics.bpm_n_total_strict,
            "n_predicted": metrics.bpm_n_predicted,
            "n_omitted": metrics.bpm_n_omitted,
            "mae": metrics.bpm_mae,
            "omit_rate": metrics.bpm_omit_rate,
        },
        "key_mode": {
            "n_total_strict": metrics.key_n_total_strict,
            "n_predicted": metrics.key_n_predicted,
            "n_omitted": metrics.key_n_omitted,
            "accuracy": metrics.key_accuracy,
            "omit_rate": metrics.key_omit_rate,
        },
        "top_bpm_errors": [
            {
                "path": err.path,
                "bpm_gt": err.bpm_gt,
                "bpm_pred": err.bpm_pred,
                "abs_error": err.abs_error,
                "candidates": err.candidates,
                "notes": err.notes,
            }
            for err in metrics.top_bpm_errors
        ],
    }


def format_text_report(metrics: EvalMetrics) -> str:
    """Format evaluation metrics as human-readable text."""
    lines = []
    lines.append("=" * 80)
    lines.append("BeetsNKeys Analysis Engine v1 - Evaluation Report")
    lines.append("=" * 80)
    lines.append("")

    # Overall stats
    lines.append("Overall:")
    lines.append(f"  Total fixtures: {metrics.total_fixtures}")
    lines.append(f"  Successful runs: {metrics.successful_runs}")
    lines.append(f"  Failed runs: {metrics.failed_runs}")
    lines.append(f"  Skipped runs: {metrics.skipped_runs}")
    lines.append("")

    # BPM metrics
    lines.append("BPM Metrics (bpm_strict fixtures only):")
    lines.append(f"  Total strict: {metrics.bpm_n_total_strict}")
    lines.append(f"  Predicted: {metrics.bpm_n_predicted}")
    lines.append(f"  Omitted: {metrics.bpm_n_omitted}")
    if metrics.bpm_mae is not None:
        lines.append(f"  MAE: {metrics.bpm_mae:.2f} BPM")
    else:
        lines.append("  MAE: N/A (no predictions with ground truth)")
    if metrics.bpm_omit_rate is not None:
        lines.append(f"  Omit rate: {metrics.bpm_omit_rate * 100:.1f}%")
    else:
        lines.append("  Omit rate: N/A")
    lines.append("")

    # Top BPM errors
    if metrics.top_bpm_errors:
        lines.append(f"Top {len(metrics.top_bpm_errors)} Worst BPM Errors:")
        lines.append("-" * 80)
        for i, err in enumerate(metrics.top_bpm_errors, start=1):
            lines.append(f"{i}. {err.path}")
            lines.append(f"   GT: {err.bpm_gt:.1f} BPM")
            if err.bpm_pred is not None:
                lines.append(f"   Predicted: {err.bpm_pred} BPM")
            else:
                lines.append("   Predicted: (omitted)")
            lines.append(f"   Error: {err.abs_error:.1f} BPM")
            if err.candidates:
                cands_str = ", ".join(str(c) for c in err.candidates[:5])
                lines.append(f"   Candidates: [{cands_str}]")
            if err.notes:
                lines.append(f"   Notes: {err.notes}")
            lines.append("")
    else:
        lines.append("No BPM errors to report (no predictions with ground truth).")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)
