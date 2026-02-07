from __future__ import annotations

from typing import Any

from engine.core.config import EngineConfig
from engine.features.types import FeatureContext
from engine.observability import hooks


def _fold_into_range(bpm: float, *, lo: float, hi: float) -> float:
    """
    Fold a BPM estimate into a musically sensible range using half/double steps.

    This is not "correctness"; it's normalization. The raw estimate can still be
    ambiguous (70 vs 140) and we preserve that ambiguity via candidates.
    """
    x = float(bpm)
    if x <= 0:
        return x
    # Prevent infinite loops on extreme values.
    for _ in range(16):
        if x < lo:
            x *= 2.0
            continue
        if x > hi:
            x /= 2.0
            continue
        break
    return x


def _windows_from_ctx(ctx: FeatureContext) -> list[float]:
    if ctx.bpm_hint_windows:
        return [float(x) for x in ctx.bpm_hint_windows]
    if ctx.bpm_hint_exact is None:
        return []

    # Deterministic fallback: treat the hint as stable across windows.
    # We keep at least 3 windows for stability scoring, unless audio is very short.
    dur = float(getattr(ctx.audio, "duration_seconds", 0.0) or 0.0)
    n = 2 if dur and dur < 6.0 else 3
    return [float(ctx.bpm_hint_exact)] * n


def _relation_to_base(bpm: int, base: int) -> str:
    if base <= 0:
        return "normal"
    if abs(bpm - int(round(base / 2))) <= 1:
        return "half"
    if abs(bpm - (base * 2)) <= 1:
        return "double"
    return "normal"


def _ensure_top_n_candidates(
    *,
    candidates: list[int],
    base: int,
    lo: int,
    hi: int,
    n: int,
) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()

    def push(v: int) -> None:
        if v < lo or v > hi:
            return
        if v in seen:
            return
        seen.add(v)
        out.append(v)

    for v in candidates:
        push(v)

    # Half/double of base as explicit ambiguity candidates.
    push(base)
    push(base * 2)
    push(int(round(base / 2)))

    # Nearby tempos (defense-in-depth for stubs; real engine would use peak picking).
    for d in (1, -1, 2, -2, 3, -3, 4, -4):
        if len(out) >= n:
            break
        push(base + d)

    return out[: max(n, 1)]


def _score_candidate_from_windows(candidate: int, windows_folded: list[int]) -> float:
    if not windows_folded:
        return 0.0

    # Support is frequency of exact (rounded) matches after folding.
    support = windows_folded.count(candidate) / float(len(windows_folded))

    # Closeness is average absolute distance (in BPM) mapped into [0, 1].
    mean_abs = sum(abs(candidate - w) for w in windows_folded) / float(len(windows_folded))
    closeness = 1.0 - min(1.0, mean_abs / 10.0)

    score = (0.7 * support) + (0.3 * closeness)
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


def _confidence_level(
    *,
    score_gap: float,
    stability: float,
    duration_seconds: float,
    config: EngineConfig,
) -> str:
    # Tunables (fallback to stable defaults if fields don't exist yet).
    gap_med = float(getattr(config.tunables, "bpm_gap_min_medium", 0.12))
    gap_high = float(getattr(config.tunables, "bpm_gap_min_high", 0.20))
    stab_med = float(getattr(config.tunables, "bpm_stability_min_medium", 0.60))
    stab_high = float(getattr(config.tunables, "bpm_stability_min_high", 0.75))
    min_dur_med = float(getattr(config.tunables, "bpm_min_duration_seconds_medium", 4.0))
    min_dur_high = float(getattr(config.tunables, "bpm_min_duration_seconds_high", 6.0))

    if duration_seconds >= min_dur_high and score_gap >= gap_high and stability >= stab_high:
        return "high"
    if duration_seconds >= min_dur_med and score_gap >= gap_med and stability >= stab_med:
        return "medium"
    return "low"


def extract_bpm_v1(ctx: FeatureContext, *, config: EngineConfig) -> dict[str, Any] | None:
    """
    Candidate-first BPM extractor (Engine v1).

    Principles:
    - Do not lie: if ambiguous/unstable, omit final value.
    - Always return candidates when available.

    Notes:
    - v1 currently operates without PCM. Candidates and stability are derived from
      deterministic hints / window hints used by tests and future integrations.
    """
    if not ctx.has_rhythm_evidence:
        hooks.emit(
            "feature_omitted",
            feature="bpm",
            reason="confidence_below_threshold",
            stage="feature:bpm",
        )
        return None

    windows_raw = _windows_from_ctx(ctx)
    if not windows_raw:
        hooks.emit(
            "feature_omitted",
            feature="bpm",
            reason="confidence_below_threshold",
            stage="feature:bpm",
        )
        return None

    lo_bpm = int(getattr(config.tunables, "bpm_normalize_min", 60))
    hi_bpm = int(getattr(config.tunables, "bpm_normalize_max", 200))

    windows_folded_f = [_fold_into_range(x, lo=lo_bpm, hi=hi_bpm) for x in windows_raw]
    windows_folded = [int(round(x)) for x in windows_folded_f if x > 0]
    if not windows_folded:
        hooks.emit(
            "feature_omitted",
            feature="bpm",
            reason="confidence_below_threshold",
            stage="feature:bpm",
        )
        return None

    # Histogram by folded-rounded BPM.
    counts: dict[int, int] = {}
    for w in windows_folded:
        counts[w] = counts.get(w, 0) + 1

    # Base ordering: count desc, then bpm asc for deterministic ties.
    ranked_by_count = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    base_bpm = ranked_by_count[0][0]

    # Start with observed bins; then pad to top-N with half/double and nearby.
    observed = [b for b, _ in ranked_by_count]
    top_n = int(getattr(config.tunables, "bpm_candidates_top_n", 5))
    cand_bpms = _ensure_top_n_candidates(
        candidates=observed,
        base=base_bpm,
        lo=lo_bpm,
        hi=hi_bpm,
        n=max(top_n, 5),
    )

    scored = [(b, _score_candidate_from_windows(b, windows_folded)) for b in cand_bpms]
    scored.sort(key=lambda t: (-t[1], t[0]))

    # Enforce minimum count.
    scored = scored[: max(5, top_n)]

    s1 = scored[0][1]
    s2 = scored[1][1] if len(scored) > 1 else 0.0
    gap = float(s1 - s2)

    # Stability: fraction of windows that match the top candidate exactly.
    top_bpm = scored[0][0]
    stability = windows_folded.count(top_bpm) / float(len(windows_folded))

    duration_seconds = float(getattr(ctx.audio, "duration_seconds", 0.0) or 0.0)
    confidence = _confidence_level(
        score_gap=gap, stability=stability, duration_seconds=duration_seconds, config=config
    )

    if confidence == "low":
        hooks.emit(
            "feature_omitted",
            feature="bpm",
            reason="confidence_below_threshold",
            stage="feature:bpm",
        )

    candidates_out = []
    for i, (bpm, score) in enumerate(scored):
        candidates_out.append(
            {
                "value": {"value_rounded": int(bpm)},
                "rank": i + 1,
                "score": float(round(score, 4)),
                "relation": _relation_to_base(int(bpm), int(top_bpm)),
            }
        )

    out: dict[str, Any] = {
        "confidence": confidence,
        "candidates": candidates_out,
        "method": "tempo_candidates_v1",
        "limits": "v1 is candidate-first and will omit bpm.value when ambiguous or unstable.",
    }

    if confidence != "low":
        # Value is derived from the top candidate; exact is the mean of folded
        # window values supporting it.
        supporting = [w for w in windows_folded_f if int(round(w)) == top_bpm]
        exact = sum(supporting) / float(len(supporting)) if supporting else float(top_bpm)
        out["value"] = {"value_exact": float(exact), "value_rounded": int(round(exact))}

    return out
