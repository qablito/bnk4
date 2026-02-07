from __future__ import annotations

from typing import Any

from engine.core.config import EngineConfig
from engine.features.types import FeatureContext
from engine.observability import hooks


def _round_bpm(x: float) -> int:
    # v1 rule: round()
    return int(round(x))


def _half_double_candidates(bpm_rounded: int) -> list[int]:
    # returns [bpm, double, half] with uniqueness
    vals = [bpm_rounded, bpm_rounded * 2, max(1, int(round(bpm_rounded / 2)))]
    out = []
    for v in vals:
        if v not in out:
            out.append(v)
    return out


def extract_bpm_v1(ctx: FeatureContext, *, config: EngineConfig) -> dict[str, Any] | None:
    """
    Returns the unlocked BPM metric block (Precision Contract shape) or None (omit).
    In v1 stubs:
      - If ctx.has_rhythm_evidence is False -> omit
      - Confidence is simulated:
          - if bpm_hint_exact is provided -> 0.8
          - else -> 0.2 (omit by threshold)
    """
    if not ctx.has_rhythm_evidence:
        return None

    if ctx.bpm_hint_exact is None:
        confidence = 0.2
        if confidence < config.tunables.bpm_min_confidence_omit:
            hooks.emit(
                "feature_omitted",
                feature="bpm",
                reason="confidence_below_threshold",
                stage="feature:bpm",
            )
            return None
        # (unreachable with defaults, but keep consistent)
        bpm_exact = 120.0
    else:
        bpm_exact = float(ctx.bpm_hint_exact)
        confidence = 0.8

    if confidence < config.tunables.bpm_min_confidence_omit:
        hooks.emit(
            "feature_omitted",
            feature="bpm",
            reason="confidence_below_threshold",
            stage="feature:bpm",
        )
        return None

    bpm_rounded = _round_bpm(bpm_exact)

    # Candidate inclusion rule: in real impl we'd compare scores; for stubs we include
    # half/double only when the delta rule would allow. Simulate as allowed when confidence < 0.9
    candidates_vals = _half_double_candidates(bpm_rounded)
    candidates = [
        {"value": {"value_rounded": v}, "rank": i + 1} for i, v in enumerate(candidates_vals[:2])
    ]

    return {
        "value": {"value_exact": bpm_exact, "value_rounded": bpm_rounded},
        "confidence": confidence,
        "candidates": candidates,
        "method": "tempo_estimation_v1",
        "limits": "Stub v1: deterministic; real tempo estimation not implemented yet.",
    }
