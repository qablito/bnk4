from __future__ import annotations

from typing import Any

from engine.core.config import EngineConfig
from engine.features.types import FeatureContext
from engine.observability import hooks


def _windows_from_ctx(ctx: FeatureContext) -> list[str]:
    if ctx.key_mode_hint_windows:
        return [str(x) for x in ctx.key_mode_hint_windows]
    if ctx.key_mode_hint is None:
        return []

    # Deterministic fallback: treat the hint as stable across windows.
    # We keep at least 3 windows for stability scoring, unless audio is very short.
    dur = float(getattr(ctx.audio, "duration_seconds", 0.0) or 0.0)
    n = 2 if dur and dur < 6.0 else 3
    return [str(ctx.key_mode_hint)] * n


def _canonicalize_key_mode(v: str) -> str:
    s = " ".join(str(v).strip().split())
    lower = s.lower()
    if lower.endswith(" major"):
        return s[:-6].strip() + " major"
    if lower.endswith(" minor"):
        return s[:-6].strip() + " minor"
    return s


def _confidence_level(
    *,
    score_gap: float,
    stability: float,
    duration_seconds: float,
    config: EngineConfig,
) -> str:
    gap_med = float(getattr(config.tunables, "key_mode_gap_min_medium", 0.20))
    gap_high = float(getattr(config.tunables, "key_mode_gap_min_high", 0.30))
    stab_med = float(getattr(config.tunables, "key_mode_stability_min_medium", 0.60))
    stab_high = float(getattr(config.tunables, "key_mode_stability_min_high", 0.75))
    min_dur_med = float(getattr(config.tunables, "key_mode_min_duration_seconds_medium", 4.0))
    min_dur_high = float(getattr(config.tunables, "key_mode_min_duration_seconds_high", 6.0))

    if duration_seconds >= min_dur_high and score_gap >= gap_high and stability >= stab_high:
        return "high"
    if duration_seconds >= min_dur_med and score_gap >= gap_med and stability >= stab_med:
        return "medium"
    return "low"


def extract_key_mode_v1(ctx: FeatureContext, *, config: EngineConfig) -> dict[str, Any] | None:
    """
    Candidate-first key/mode extractor (Engine v1).

    Principles:
    - Do not lie: if ambiguous/unstable, omit final value.
    - Always return candidates when available.

    Notes:
    - v1 currently operates without PCM. Candidates and stability are derived from
      deterministic hints / window hints used by tests and future integrations.
    """
    if not ctx.has_tonal_evidence:
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )
        return None

    windows_raw = _windows_from_ctx(ctx)
    if not windows_raw:
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )
        return None

    windows = [_canonicalize_key_mode(x) for x in windows_raw if str(x).strip()]
    if not windows:
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )
        return None

    counts: dict[str, int] = {}
    for w in windows:
        counts[w] = counts.get(w, 0) + 1

    scored = [(k, counts[k] / float(len(windows))) for k in counts]
    scored.sort(key=lambda t: (-t[1], t[0]))

    top_n = int(getattr(config.tunables, "key_mode_candidates_top_n", 5))
    scored = scored[: max(1, top_n)]

    s1 = scored[0][1]
    s2 = scored[1][1] if len(scored) > 1 else 0.0
    gap = float(s1 - s2)
    stability = float(s1)
    duration_seconds = float(getattr(ctx.audio, "duration_seconds", 0.0) or 0.0)

    confidence = _confidence_level(
        score_gap=gap,
        stability=stability,
        duration_seconds=duration_seconds,
        config=config,
    )

    if confidence == "low":
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )

    candidates_out = []
    for i, (value, score) in enumerate(scored):
        candidates_out.append({"value": value, "rank": i + 1, "score": float(round(score, 4))})

    out: dict[str, Any] = {
        "confidence": confidence,
        "candidates": candidates_out,
        "method": "key_mode_candidates_v1",
        "limits": "v1 is candidate-first and will omit key_mode.value when ambiguous or unstable.",
    }

    if confidence != "low":
        out["value"] = scored[0][0]

    return out
