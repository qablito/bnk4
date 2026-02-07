"""Run analysis on fixtures and collect predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from engine.core.errors import EngineError
from engine.eval.eval_types import Fixture, PredictionResult
from engine.pipeline.run import run_analysis_v1

Role = Literal["guest", "free", "pro"]


def run_fixture(
    fixture: Fixture,
    *,
    role: Role = "pro",
    fail_on_missing: bool = False,
) -> PredictionResult:
    """
    Run analysis on a single fixture and extract predictions.

    Args:
        fixture: Ground truth fixture.
        role: Analysis role (guest/free/pro). Default: pro for full output.
        fail_on_missing: If True, raise error when audio file missing.
                         If False, skip and record.

    Returns:
        PredictionResult with extracted predictions.
    """
    # Check if file exists
    audio_path = Path(fixture.path)
    if not audio_path.exists():
        if fail_on_missing:
            raise FileNotFoundError(f"Audio file not found: {fixture.path}")
        return PredictionResult(
            fixture=fixture,
            success=False,
            error=None,
            output=None,
            skipped=True,
            skip_reason=f"File not found: {fixture.path}",
        )

    # Run analysis
    try:
        output = run_analysis_v1(input_path=str(audio_path), role=role)
        success = True
        error = None
    except EngineError as exc:
        output = None
        success = False
        error = f"{exc.code}: {exc.message}"
    except Exception as exc:
        output = None
        success = False
        error = f"Unexpected error: {type(exc).__name__}: {exc}"

    # Extract predictions
    result = PredictionResult(
        fixture=fixture,
        success=success,
        error=error,
        output=output,
        skipped=False,
        skip_reason=None,
    )

    if output is not None and "metrics" in output:
        metrics = output["metrics"]
        _extract_bpm(result, metrics)
        _extract_key_mode(result, metrics)

    return result


def _extract_bpm(result: PredictionResult, metrics: dict) -> None:
    """Extract BPM prediction from metrics."""
    if "bpm" not in metrics:
        result.bpm_omitted = True
        return

    bpm_block = metrics["bpm"]
    if bpm_block.get("locked"):
        result.bpm_omitted = True
        return

    val = bpm_block.get("value")
    if val is None:
        result.bpm_omitted = True
        return

    if isinstance(val, dict):
        result.bpm_value_rounded = val.get("value_rounded")
        result.bpm_value_exact = val.get("value_exact")
    elif isinstance(val, (int, float)):
        result.bpm_value_rounded = int(round(val))
        result.bpm_value_exact = float(val)

    result.bpm_omitted = result.bpm_value_rounded is None

    # Extract candidates
    candidates = bpm_block.get("candidates")
    if candidates and isinstance(candidates, list):
        result.bpm_candidates = candidates


def _extract_key_mode(result: PredictionResult, metrics: dict) -> None:
    """Extract key/mode prediction from metrics."""
    if "key_mode" not in metrics:
        result.key_mode_omitted = True
        return

    km_block = metrics["key_mode"]
    if km_block.get("locked"):
        result.key_mode_omitted = True
        return

    val = km_block.get("value")
    if val is None or not isinstance(val, dict):
        result.key_mode_omitted = True
        return

    result.key_value = val.get("key")
    result.mode_value = val.get("mode")
    result.key_mode_omitted = result.key_value is None


def run_all_fixtures(
    fixtures: list[Fixture],
    *,
    role: Role = "pro",
    limit: int | None = None,
    fail_on_missing: bool = False,
) -> list[PredictionResult]:
    """
    Run analysis on all fixtures.

    Args:
        fixtures: List of fixtures to evaluate.
        role: Analysis role.
        limit: Optional limit on number of fixtures to process.
        fail_on_missing: If True, raise error when audio file missing.

    Returns:
        List of prediction results (same order as fixtures).
    """
    if limit is not None:
        fixtures = fixtures[:limit]

    results = []
    for fixture in fixtures:
        result = run_fixture(fixture, role=role, fail_on_missing=fail_on_missing)
        results.append(result)
    return results
