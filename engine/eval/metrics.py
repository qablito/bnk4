"""Compute evaluation metrics."""

from __future__ import annotations

from typing import Any

from engine.eval.eval_types import (
    BpmError,
    BpmHalfDoubleConfusion,
    EvalMetrics,
    KeyModeError,
    PredictionResult,
)


def compute_metrics(
    results: list[PredictionResult],
    *,
    top_n_errors: int = 20,
    bpm_tolerance: float = 1.0,
    top_n_confusions: int = 10,
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

    def _close(a: float, b: float) -> bool:
        return abs(float(a) - float(b)) <= float(bpm_tolerance)

    def _candidate_values_rounded(r: PredictionResult) -> list[int] | None:
        if not r.bpm_candidates:
            return None
        out: list[int] = []
        for c in r.bpm_candidates:
            val = c.get("value", {})
            if isinstance(val, dict):
                vr = val.get("value_rounded")
                if vr is not None:
                    out.append(int(vr))
            elif isinstance(val, (int, float)):
                out.append(int(round(val)))
        return out or None

    def _compute_bpm_section(
        *,
        kind: str,
        gt_selector,
        pred_selector,
        omitted_selector,
    ) -> tuple[int, int, int, float | None, float | None, list[BpmError]]:
        strict_with_gt = [r for r in bpm_strict_results if gt_selector(r.fixture) is not None]
        n_total = len(strict_with_gt)
        predicted = [
            r
            for r in strict_with_gt
            if (not omitted_selector(r)) and (pred_selector(r) is not None)
        ]
        n_pred = len(predicted)
        n_omit = n_total - n_pred
        omit_rate = (n_omit / n_total) if n_total > 0 else None

        errors: list[BpmError] = []
        abs_errors: list[float] = []
        for r in predicted:
            gt = gt_selector(r.fixture)
            if gt is None:
                continue
            pred = pred_selector(r)
            if pred is None:
                continue
            ae = abs(float(pred) - float(gt))
            abs_errors.append(ae)
            errors.append(
                BpmError(
                    path=r.fixture.path,
                    bpm_gt=float(gt),
                    bpm_pred=int(pred),
                    abs_error=float(ae),
                    candidates=_candidate_values_rounded(r),
                    notes=r.fixture.notes,
                    kind="raw" if kind == "raw" else "reportable",
                )
            )
        mae = (sum(abs_errors) / float(len(abs_errors))) if abs_errors else None
        return n_total, n_pred, n_omit, mae, omit_rate, errors

    (
        bpm_reportable_n_total_strict,
        bpm_reportable_n_predicted,
        bpm_reportable_n_omitted,
        bpm_reportable_mae,
        bpm_reportable_omit_rate,
        bpm_errors_reportable,
    ) = _compute_bpm_section(
        kind="reportable",
        gt_selector=lambda f: f.bpm_gt_reportable,
        pred_selector=lambda r: r.bpm_value_rounded,
        omitted_selector=lambda r: r.bpm_omitted,
    )

    (
        bpm_raw_n_total_strict,
        bpm_raw_n_predicted,
        bpm_raw_n_omitted,
        bpm_raw_mae,
        bpm_raw_omit_rate,
        bpm_errors_raw,
    ) = _compute_bpm_section(
        kind="raw",
        gt_selector=lambda f: f.bpm_gt_raw,
        pred_selector=lambda r: r.bpm_raw_value_rounded,
        omitted_selector=lambda r: r.bpm_raw_omitted,
    )

    # Family match rate for reportable BPM:
    # counts a match if pred ~= gt OR pred ~= 2*gt OR pred ~= 0.5*gt (within tolerance).
    reportable_with_gt = [r for r in bpm_strict_results if r.fixture.bpm_gt_reportable is not None]
    reportable_predicted = [
        r for r in reportable_with_gt if (not r.bpm_omitted) and (r.bpm_value_rounded is not None)
    ]

    def _family_match(pred: float, gt: float) -> bool:
        return _close(pred, gt) or _close(pred, 2.0 * gt) or _close(2.0 * pred, gt)

    bpm_family_match_rate_reportable = (
        sum(
            1
            for r in reportable_predicted
            if _family_match(float(r.bpm_value_rounded), float(r.fixture.bpm_gt_reportable))  # type: ignore[arg-type]
        )
        / float(len(reportable_predicted))
        if reportable_predicted
        else None
    )

    # Omit reason breakdown for reportable (strict fixtures with reportable GT only).
    bpm_reportable_omit_reason_counts: dict[str, int] = {}
    for r in reportable_with_gt:
        if not r.bpm_omitted:
            continue
        omitted_codes = [c for c in (r.bpm_reason_codes or []) if str(c).startswith("omitted_")]
        if not omitted_codes:
            omitted_codes = ["omitted_unknown"]
        for code in omitted_codes:
            k = str(code)
            bpm_reportable_omit_reason_counts[k] = bpm_reportable_omit_reason_counts.get(k, 0) + 1
    bpm_reportable_omit_reason_counts = dict(sorted(bpm_reportable_omit_reason_counts.items()))

    # Policy flip rate: among emitted reportable values with raw predictions,
    # how often does reportable differ from raw by more than tolerance?
    flip_eligible = [
        r
        for r in reportable_predicted
        if (not r.bpm_raw_omitted) and (r.bpm_raw_value_rounded is not None)
    ]
    bpm_policy_flip_rate = (
        sum(
            1
            for r in flip_eligible
            if not _close(float(r.bpm_value_rounded), float(r.bpm_raw_value_rounded))  # type: ignore[arg-type]
        )
        / float(len(flip_eligible))
        if flip_eligible
        else None
    )

    # Sort BPM errors by abs_error descending, take top N
    bpm_errors_reportable.sort(key=lambda e: e.abs_error, reverse=True)
    bpm_errors_raw.sort(key=lambda e: e.abs_error, reverse=True)
    top_bpm_errors_reportable = bpm_errors_reportable[:top_n_errors]
    top_bpm_errors_raw = bpm_errors_raw[:top_n_errors]

    # Raw/reportable confusion stats (all successful BPM predictions, strict or not).
    confusions: list[BpmHalfDoubleConfusion] = []
    confusion_matrix = {
        "pred_matches_raw": 0,
        "pred_matches_reportable": 0,
        "pred_matches_both": 0,
        "pred_matches_neither": 0,
        "gt_missing": 0,
    }
    bpm_confusion_results = [
        r
        for r in results
        if r.success and not r.skipped and (not r.bpm_omitted) and (r.bpm_value_rounded is not None)
    ]

    for r in bpm_confusion_results:
        raw = r.fixture.bpm_gt_raw
        rep = r.fixture.bpm_gt_reportable
        if raw is None and rep is None:
            confusion_matrix["gt_missing"] += 1
            continue
        pred = float(r.bpm_value_rounded)

        matches_raw = raw is not None and _close(pred, float(raw))
        matches_rep = rep is not None and _close(pred, float(rep))
        if matches_raw and matches_rep:
            confusion_matrix["pred_matches_both"] += 1
        elif matches_raw and not matches_rep:
            confusion_matrix["pred_matches_raw"] += 1
            if raw is not None and rep is not None:
                confusions.append(
                    BpmHalfDoubleConfusion(
                        path=r.fixture.path,
                        bpm_gt_raw=float(raw),
                        bpm_gt_reportable=float(rep),
                        bpm_pred=int(round(pred)),
                        relation="pred_matches_raw",
                        candidates=_candidate_values_rounded(r),
                        notes=r.fixture.notes,
                    )
                )
        elif matches_rep and not matches_raw:
            confusion_matrix["pred_matches_reportable"] += 1
            if raw is not None and rep is not None:
                confusions.append(
                    BpmHalfDoubleConfusion(
                        path=r.fixture.path,
                        bpm_gt_raw=float(raw),
                        bpm_gt_reportable=float(rep),
                        bpm_pred=int(round(pred)),
                        relation="pred_matches_reportable",
                        candidates=_candidate_values_rounded(r),
                        notes=r.fixture.notes,
                    )
                )

        else:
            confusion_matrix["pred_matches_neither"] += 1

    confusions.sort(key=lambda c: c.path)
    if top_n_confusions >= 0:
        confusions = confusions[:top_n_confusions]
    bpm_half_double_confusion_count = len(confusions)

    # Key/mode strict metrics.
    key_strict_results = [
        r
        for r in results
        if r.success
        and not r.skipped
        and r.fixture.is_key_strict
        and r.fixture.key_gt is not None
        and r.fixture.mode_gt is not None
    ]
    key_n_total_strict = len(key_strict_results)
    key_predicted_rows = [
        r
        for r in key_strict_results
        if (not r.key_mode_omitted) and (r.key_value is not None) and (r.mode_value is not None)
    ]
    key_n_predicted = len(key_predicted_rows)
    key_n_omitted = key_n_total_strict - key_n_predicted
    key_omit_rate = (key_n_omitted / float(key_n_total_strict)) if key_n_total_strict > 0 else None

    key_correct_count = 0
    mode_correct_count = 0
    both_correct_count = 0
    key_errors: list[KeyModeError] = []
    key_confusion_counts = {
        "wrong_key": 0,
        "wrong_mode": 0,
        "both_wrong": 0,
    }
    for r in key_predicted_rows:
        key_gt = str(r.fixture.key_gt)
        mode_gt = str(r.fixture.mode_gt).lower()
        key_pred = str(r.key_value)
        mode_pred = str(r.mode_value).lower()
        key_ok = key_pred == key_gt
        mode_ok = mode_pred == mode_gt
        if key_ok:
            key_correct_count += 1
        if mode_ok:
            mode_correct_count += 1
        if key_ok and mode_ok:
            both_correct_count += 1
            continue

        if (not key_ok) and mode_ok:
            mismatch = "wrong_key"
        elif key_ok and (not mode_ok):
            mismatch = "wrong_mode"
        else:
            mismatch = "both_wrong"
        key_confusion_counts[mismatch] += 1
        key_errors.append(
            KeyModeError(
                path=r.fixture.path,
                key_gt=key_gt,
                mode_gt=mode_gt,
                key_pred=key_pred,
                mode_pred=mode_pred,
                mismatch=mismatch,
                candidates=r.key_candidates,
                notes=r.fixture.notes,
            )
        )

    key_accuracy = key_correct_count / float(key_n_predicted) if key_n_predicted > 0 else None
    key_mode_accuracy = mode_correct_count / float(key_n_predicted) if key_n_predicted > 0 else None
    key_both_accuracy = both_correct_count / float(key_n_predicted) if key_n_predicted > 0 else None
    key_errors.sort(key=lambda e: e.path)
    top_key_mode_errors = key_errors[: max(0, int(top_n_errors))]

    return EvalMetrics(
        total_fixtures=total,
        successful_runs=successful,
        failed_runs=failed,
        skipped_runs=skipped,
        bpm_reportable_n_total_strict=bpm_reportable_n_total_strict,
        bpm_reportable_n_predicted=bpm_reportable_n_predicted,
        bpm_reportable_n_omitted=bpm_reportable_n_omitted,
        bpm_reportable_mae=bpm_reportable_mae,
        bpm_reportable_omit_rate=bpm_reportable_omit_rate,
        bpm_family_match_rate_reportable=bpm_family_match_rate_reportable,
        bpm_reportable_omit_reason_counts=bpm_reportable_omit_reason_counts,
        bpm_policy_flip_rate=bpm_policy_flip_rate,
        bpm_raw_n_total_strict=bpm_raw_n_total_strict,
        bpm_raw_n_predicted=bpm_raw_n_predicted,
        bpm_raw_n_omitted=bpm_raw_n_omitted,
        bpm_raw_mae=bpm_raw_mae,
        bpm_raw_omit_rate=bpm_raw_omit_rate,
        top_bpm_errors_reportable=top_bpm_errors_reportable,
        top_bpm_errors_raw=top_bpm_errors_raw,
        bpm_half_double_confusion_count=bpm_half_double_confusion_count,
        bpm_half_double_confusions=confusions,
        bpm_half_double_confusion_matrix=confusion_matrix,
        key_n_total_strict=key_n_total_strict,
        key_n_predicted=key_n_predicted,
        key_n_omitted=key_n_omitted,
        key_accuracy=key_accuracy,
        key_mode_accuracy=key_mode_accuracy,
        key_both_accuracy=key_both_accuracy,
        key_omit_rate=key_omit_rate,
        key_confusion_counts=key_confusion_counts,
        top_key_mode_errors=top_key_mode_errors,
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
        # Back-compat alias: `bpm` matches the old single-GT section (reportable).
        "bpm": {
            "n_total_strict": metrics.bpm_reportable_n_total_strict,
            "n_predicted": metrics.bpm_reportable_n_predicted,
            "n_omitted": metrics.bpm_reportable_n_omitted,
            "mae": metrics.bpm_reportable_mae,
            "omit_rate": metrics.bpm_reportable_omit_rate,
            "family_match_rate": metrics.bpm_family_match_rate_reportable,
            "omit_reason_counts": metrics.bpm_reportable_omit_reason_counts,
            "policy_flip_rate": metrics.bpm_policy_flip_rate,
        },
        "bpm_reportable": {
            "n_total_strict": metrics.bpm_reportable_n_total_strict,
            "n_predicted": metrics.bpm_reportable_n_predicted,
            "n_omitted": metrics.bpm_reportable_n_omitted,
            "mae": metrics.bpm_reportable_mae,
            "omit_rate": metrics.bpm_reportable_omit_rate,
            "family_match_rate": metrics.bpm_family_match_rate_reportable,
            "omit_reason_counts": metrics.bpm_reportable_omit_reason_counts,
            "policy_flip_rate": metrics.bpm_policy_flip_rate,
        },
        "bpm_raw": {
            "n_total_strict": metrics.bpm_raw_n_total_strict,
            "n_predicted": metrics.bpm_raw_n_predicted,
            "n_omitted": metrics.bpm_raw_n_omitted,
            "mae": metrics.bpm_raw_mae,
            "omit_rate": metrics.bpm_raw_omit_rate,
        },
        "bpm_half_double_confusions": [
            {
                "path": c.path,
                "bpm_gt_raw": c.bpm_gt_raw,
                "bpm_gt_reportable": c.bpm_gt_reportable,
                "bpm_pred": c.bpm_pred,
                "relation": c.relation,
                "candidates": c.candidates,
                "notes": c.notes,
            }
            for c in metrics.bpm_half_double_confusions
        ],
        "bpm_half_double_confusion_count": metrics.bpm_half_double_confusion_count,
        "bpm_half_double_confusion_matrix": metrics.bpm_half_double_confusion_matrix,
        "key_mode": {
            "n_total_strict": metrics.key_n_total_strict,
            "n_predicted": metrics.key_n_predicted,
            "n_omitted": metrics.key_n_omitted,
            # Back-compat alias: "accuracy" now means both key+mode correct.
            "accuracy": metrics.key_both_accuracy,
            "accuracy_key": metrics.key_accuracy,
            "accuracy_mode": metrics.key_mode_accuracy,
            "accuracy_both": metrics.key_both_accuracy,
            "omit_rate": metrics.key_omit_rate,
            "confusion_counts": dict(sorted(metrics.key_confusion_counts.items())),
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
            for err in metrics.top_bpm_errors_reportable
        ],
        "top_bpm_errors_raw": [
            {
                "path": err.path,
                "bpm_gt": err.bpm_gt,
                "bpm_pred": err.bpm_pred,
                "abs_error": err.abs_error,
                "candidates": err.candidates,
                "notes": err.notes,
            }
            for err in metrics.top_bpm_errors_raw
        ],
        "top_key_mode_errors": [
            {
                "path": err.path,
                "key_gt": err.key_gt,
                "mode_gt": err.mode_gt,
                "key_pred": err.key_pred,
                "mode_pred": err.mode_pred,
                "mismatch": err.mismatch,
                "candidates": err.candidates,
                "notes": err.notes,
            }
            for err in metrics.top_key_mode_errors
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
    lines.append("  Reportable:")
    lines.append(f"    Total strict: {metrics.bpm_reportable_n_total_strict}")
    lines.append(f"    Predicted: {metrics.bpm_reportable_n_predicted}")
    lines.append(f"    Omitted: {metrics.bpm_reportable_n_omitted}")
    if metrics.bpm_reportable_mae is not None:
        lines.append(f"    MAE: {metrics.bpm_reportable_mae:.2f} BPM")
    else:
        lines.append("    MAE: N/A (no predictions with ground truth)")
    if metrics.bpm_reportable_omit_rate is not None:
        lines.append(f"    Omit rate: {metrics.bpm_reportable_omit_rate * 100:.1f}%")
    else:
        lines.append("    Omit rate: N/A")
    if metrics.bpm_family_match_rate_reportable is not None:
        lines.append(
            f"    Family match rate: {metrics.bpm_family_match_rate_reportable * 100:.1f}%"
        )
    if metrics.bpm_policy_flip_rate is not None:
        lines.append(f"    Policy flip rate: {metrics.bpm_policy_flip_rate * 100:.1f}%")
    if metrics.bpm_reportable_omit_reason_counts:
        lines.append("    Omit reasons:")
        for code, count in metrics.bpm_reportable_omit_reason_counts.items():
            lines.append(f"      - {code}: {count}")

    lines.append("  Raw:")
    lines.append(f"    Total strict: {metrics.bpm_raw_n_total_strict}")
    lines.append(f"    Predicted: {metrics.bpm_raw_n_predicted}")
    lines.append(f"    Omitted: {metrics.bpm_raw_n_omitted}")
    if metrics.bpm_raw_mae is not None:
        lines.append(f"    MAE: {metrics.bpm_raw_mae:.2f} BPM")
    else:
        lines.append("    MAE: N/A (no predictions with ground truth)")
    if metrics.bpm_raw_omit_rate is not None:
        lines.append(f"    Omit rate: {metrics.bpm_raw_omit_rate * 100:.1f}%")
    else:
        lines.append("    Omit rate: N/A")

    if metrics.bpm_half_double_confusion_count:
        lines.append("")
        lines.append("Raw vs Reportable Confusions:")
        lines.append(f"  Count: {metrics.bpm_half_double_confusion_count}")
        if metrics.bpm_half_double_confusion_matrix:
            lines.append("  Match matrix:")
            for k, v in metrics.bpm_half_double_confusion_matrix.items():
                lines.append(f"    - {k}: {v}")
    lines.append("")

    # Key/mode metrics
    lines.append("Key/Mode Metrics (key_strict fixtures only):")
    lines.append(f"  Total strict: {metrics.key_n_total_strict}")
    lines.append(f"  Predicted: {metrics.key_n_predicted}")
    lines.append(f"  Omitted: {metrics.key_n_omitted}")
    if metrics.key_omit_rate is not None:
        lines.append(f"  Omit rate: {metrics.key_omit_rate * 100:.1f}%")
    else:
        lines.append("  Omit rate: N/A")
    if metrics.key_accuracy is not None:
        lines.append(f"  Accuracy (key): {metrics.key_accuracy * 100:.1f}%")
    else:
        lines.append("  Accuracy (key): N/A")
    if metrics.key_mode_accuracy is not None:
        lines.append(f"  Accuracy (mode): {metrics.key_mode_accuracy * 100:.1f}%")
    else:
        lines.append("  Accuracy (mode): N/A")
    if metrics.key_both_accuracy is not None:
        lines.append(f"  Accuracy (both): {metrics.key_both_accuracy * 100:.1f}%")
    else:
        lines.append("  Accuracy (both): N/A")
    if metrics.key_confusion_counts:
        lines.append("  Confusions:")
        for k, v in sorted(metrics.key_confusion_counts.items()):
            lines.append(f"    - {k}: {v}")
    lines.append("")

    if metrics.top_key_mode_errors:
        lines.append(f"Top {len(metrics.top_key_mode_errors)} Worst Key/Mode Errors:")
        lines.append("-" * 80)
        for i, err in enumerate(metrics.top_key_mode_errors, start=1):
            lines.append(f"{i}. {err.path}")
            lines.append(f"   GT: {err.key_gt} {err.mode_gt}")
            lines.append(f"   Predicted: {err.key_pred or '—'} {err.mode_pred or '—'}")
            lines.append(f"   Mismatch: {err.mismatch}")
            if err.candidates:
                cands = []
                for c in err.candidates[:5]:
                    if isinstance(c, dict):
                        key = c.get("key")
                        mode = c.get("mode")
                        score = c.get("score")
                        if key and mode:
                            if isinstance(score, (int, float)):
                                cands.append(f"{key} {mode} ({float(score):.3f})")
                            else:
                                cands.append(f"{key} {mode}")
                if cands:
                    lines.append(f"   Candidates: [{', '.join(cands)}]")
            if err.notes:
                lines.append(f"   Notes: {err.notes}")
            lines.append("")

    # Top BPM errors (reportable)
    if metrics.top_bpm_errors_reportable:
        lines.append(f"Top {len(metrics.top_bpm_errors_reportable)} Worst BPM Errors (reportable):")
        lines.append("-" * 80)
        for i, err in enumerate(metrics.top_bpm_errors_reportable, start=1):
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

    # Half/double confusions details
    if metrics.bpm_half_double_confusions:
        lines.append(f"Top {len(metrics.bpm_half_double_confusions)} Half/Double Confusions:")
        lines.append("-" * 80)
        for i, c in enumerate(metrics.bpm_half_double_confusions, start=1):
            lines.append(f"{i}. {c.path}")
            lines.append(f"   GT raw: {c.bpm_gt_raw:.1f} BPM")
            lines.append(f"   GT reportable: {c.bpm_gt_reportable:.1f} BPM")
            lines.append(f"   Predicted: {c.bpm_pred} BPM ({c.relation})")
            if c.candidates:
                cands_str = ", ".join(str(x) for x in c.candidates[:5])
                lines.append(f"   Candidates: [{cands_str}]")
            if c.notes:
                lines.append(f"   Notes: {c.notes}")
            lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)
