"""Run analysis on fixtures and collect predictions."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any, Literal

from engine.core.errors import EngineError
from engine.eval.eval_types import Fixture, PredictionResult
from engine.pipeline.run import run_analysis_v1

Role = Literal["guest", "free", "pro"]

_TRACEBACK_SHORT_MAX_LINES = 20
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _sanitize_traceback_text(text: str) -> str:
    # Avoid leaking user paths and keep output more deterministic.
    root = str(_REPO_ROOT)
    return text.replace(root + "/", "").replace(root + "\\", "")


def _infer_stage_from_engine_error(exc: EngineError) -> str:
    ctx = exc.context or {}
    stage = ctx.get("stage")
    if isinstance(stage, str) and stage:
        return stage

    # Best-effort: decode/ingest errors generally include path/suffix context.
    if exc.code in {"UNSUPPORTED_INPUT", "INVALID_INPUT"} and any(
        k in ctx for k in ("path", "suffix")
    ):
        return "decode"

    return "run_analysis_v1"


def _format_traceback(exc: BaseException, *, full: bool) -> str:
    lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    text = _sanitize_traceback_text("".join(lines))
    if full:
        return text
    head = text.splitlines()[:_TRACEBACK_SHORT_MAX_LINES]
    return "\n".join(head)


def _make_failure_info(exc: BaseException, *, debug_traceback: bool) -> dict[str, Any]:
    stage = "run_analysis_v1"
    engine_error_code: str | None = None
    message: str

    if isinstance(exc, EngineError):
        stage = _infer_stage_from_engine_error(exc)
        engine_error_code = exc.code
        message = exc.message
    else:
        message = str(exc)

    info: dict[str, Any] = {
        "stage": stage,
        "exc_type": type(exc).__name__,
        "message": message,
        "engine_error_code": engine_error_code,
        "traceback_short": _format_traceback(exc, full=False),
    }
    if debug_traceback:
        info["traceback_full"] = _format_traceback(exc, full=True)
    return info


def run_fixture(
    fixture: Fixture,
    *,
    role: Role = "pro",
    fail_on_missing: bool = False,
    debug_traceback: bool = False,
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
            skip_reason_code="file_not_found",
        )

    # Run analysis
    try:
        output = run_analysis_v1(input_path=str(audio_path), role=role)
        success = True
        error = None
        failure = None
    except EngineError as exc:
        output = None
        success = False
        error = f"{exc.code}: {exc.message}"
        failure = _make_failure_info(exc, debug_traceback=debug_traceback)
    except Exception as exc:
        output = None
        success = False
        error = f"Unexpected error: {type(exc).__name__}: {exc}"
        failure = _make_failure_info(exc, debug_traceback=debug_traceback)

    # Extract predictions
    result = PredictionResult(
        fixture=fixture,
        success=success,
        error=error,
        output=output,
        skipped=False,
        skip_reason=None,
        skip_reason_code=None,
        failure=failure,
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
        result.bpm_raw_omitted = True
        return

    bpm_block = metrics["bpm"]

    # Preserve candidates even when bpm.value is omitted (low confidence / locked).
    candidates = bpm_block.get("candidates")
    if candidates and isinstance(candidates, list):
        result.bpm_candidates = candidates

    codes = bpm_block.get("bpm_reason_codes")
    if isinstance(codes, list):
        result.bpm_reason_codes = [str(x) for x in codes]

    structured = bpm_block.get("bpm_candidates")
    if structured and isinstance(structured, list):
        result.bpm_candidates_structured = structured

    # Raw BPM can be present even when reportable bpm.value is omitted.
    raw = bpm_block.get("bpm_raw")
    if isinstance(raw, (int, float)):
        result.bpm_raw_value_exact = float(raw)
        result.bpm_raw_value_rounded = int(round(float(raw)))
        result.bpm_raw_omitted = False
    else:
        result.bpm_raw_omitted = True

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
    fail_fast: bool = False,
    debug_traceback: bool = False,
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
        result = run_fixture(
            fixture,
            role=role,
            fail_on_missing=fail_on_missing,
            debug_traceback=debug_traceback,
        )
        results.append(result)
        if fail_fast and (not result.success and not result.skipped):
            break
    return results
