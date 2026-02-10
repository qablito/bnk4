from __future__ import annotations

from typing import Any

from engine.core.config import EngineConfig
from engine.features.types import FeatureContext
from engine.observability import hooks

_KEY_ORDER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_KEY_INDEX = {k: i for i, k in enumerate(_KEY_ORDER)}
_MODE_ORDER = ["major", "minor"]
_MODE_INDEX = {m: i for i, m in enumerate(_MODE_ORDER)}

_REASON_CODE_ORDER = [
    "omitted_ambiguous_runnerup",
    "omitted_low_confidence",
    "emit_confident",
]


def _ordered_reason_codes(codes: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for c in _REASON_CODE_ORDER:
        if c in codes and c not in seen:
            seen.add(c)
            out.append(c)
    for c in sorted(codes):
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out


def _normalize_tonic(token: str) -> str | None:
    s = str(token).strip().upper().replace("♯", "#").replace("♭", "B")
    flats_to_sharps = {
        "DB": "C#",
        "EB": "D#",
        "GB": "F#",
        "AB": "G#",
        "BB": "A#",
    }
    if s in flats_to_sharps:
        s = flats_to_sharps[s]
    if s in _KEY_INDEX:
        return s
    return None


def _parse_key_mode_label(label: str) -> tuple[str | None, str | None]:
    parts = [p for p in str(label).strip().split() if p]
    if len(parts) < 2:
        return None, None
    tonic = _normalize_tonic(parts[0])
    mode = parts[-1].lower()
    if tonic is None or mode not in _MODE_INDEX:
        return None, None
    return tonic, mode


def _windows_from_ctx(ctx: FeatureContext) -> list[tuple[str, str]]:
    if ctx.key_mode_hint_windows:
        out: list[tuple[str, str]] = []
        for x in ctx.key_mode_hint_windows:
            key, mode = _parse_key_mode_label(str(x))
            if key is not None and mode is not None:
                out.append((key, mode))
        return out
    if ctx.key_mode_hint is None:
        return []

    # Deterministic fallback: treat the hint as stable across windows.
    # We keep at least 3 windows for stability scoring, unless audio is very short.
    dur = float(getattr(ctx.audio, "duration_seconds", 0.0) or 0.0)
    n = 2 if dur and dur < 6.0 else 3
    key, mode = _parse_key_mode_label(str(ctx.key_mode_hint))
    if key is None or mode is None:
        return []
    return [(key, mode)] * n


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

    windows = _windows_from_ctx(ctx)
    if not windows:
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )
        return None

    counts: dict[tuple[str, str], int] = {}
    for w in windows:
        counts[w] = counts.get(w, 0) + 1

    scored = [((k, m), counts[(k, m)] / float(len(windows))) for k, m in counts]
    scored.sort(
        key=lambda t: (
            -t[1],
            _KEY_INDEX.get(t[0][0], 999),
            _MODE_INDEX.get(t[0][1], 999),
        )
    )

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

    ambiguous_gap = float(getattr(config.tunables, "key_mode_ambiguous_gap_max", 0.15))
    ambiguous_runner_up = bool(len(scored) > 1 and gap < ambiguous_gap)

    if confidence == "low":
        hooks.emit(
            "feature_omitted",
            feature="key_mode",
            reason="confidence_below_threshold",
            stage="feature:key_mode",
        )

    reason_codes: list[str] = []
    if ambiguous_runner_up:
        reason_codes.append("omitted_ambiguous_runnerup")
    if confidence == "low":
        reason_codes.append("omitted_low_confidence")
    if not reason_codes:
        reason_codes.append("emit_confident")
    reason_codes = _ordered_reason_codes(reason_codes)

    candidates_out = []
    for i, ((key, mode), score) in enumerate(scored):
        candidates_out.append(
            {
                "key": key,
                "mode": mode,
                "score": float(round(score, 4)),
                "family": "direct",
                "rank": i + 1,
            }
        )

    out: dict[str, Any] = {
        "value": None,
        "mode": None,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "candidates": candidates_out,
        "method": "key_mode_global_v1",
    }

    if confidence != "low" and not ambiguous_runner_up:
        out["value"] = scored[0][0][0]
        out["mode"] = scored[0][0][1]

    return out
