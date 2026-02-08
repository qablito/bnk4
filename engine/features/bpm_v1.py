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


def _windows_from_ctx(ctx: FeatureContext, *, config: EngineConfig) -> list[float]:
    # Prefer richer per-window details when available (can include multi-band hints).
    details = getattr(ctx, "bpm_hint_window_details", None)
    if details and isinstance(details, list):
        min_score = float(getattr(config.tunables, "bpm_hint_window_min_score", 0.0))
        out: list[float] = []
        for d in details:
            if not isinstance(d, dict):
                continue
            try:
                v = d.get("best_bpm")
                s = d.get("best_score")
                if s is not None and float(s) < min_score:
                    v = None
                if v is not None:
                    out.append(float(v))
            except (TypeError, ValueError):
                pass
            try:
                v = d.get("high_best_bpm")
                s = d.get("high_best_score")
                if s is not None and float(s) < min_score:
                    v = None
                if v is not None:
                    out.append(float(v))
            except (TypeError, ValueError):
                pass
        if out:
            return out

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


def _score_candidate_from_windows(
    candidate: int,
    windows_folded: list[int],
    *,
    tol_bpm: int,
    triplet_beta: float,
    triplet_min_direct: float,
) -> float:
    if not windows_folded:
        return 0.0

    # Support is frequency of matches within tolerance after folding/rounding.
    #
    # We intentionally allow small +/- jitter because real signals often wobble
    # by ~1 BPM across windows due to rounding and window boundary effects.
    tol = max(0, int(tol_bpm))
    direct = sum(1 for w in windows_folded if abs(candidate - w) <= tol)
    direct_support = direct / float(len(windows_folded))

    # Triplet/dotted ambiguity:
    # Some produced beats yield a strong 2/3 periodicity (e.g. triplet hats),
    # which can dominate naive autocorrelation and pull tempo toward ~2/3 * BPM.
    #
    # We only let 2/3 evidence contribute if there is at least *some* direct
    # evidence for the candidate tempo (otherwise 120 BPM would "support" 180).
    support = direct_support
    if direct_support >= float(triplet_min_direct):
        two_thirds = int(round(float(candidate) * (2.0 / 3.0)))
        trip = sum(1 for w in windows_folded if abs(two_thirds - w) <= tol)
        support = (direct + (float(triplet_beta) * float(trip))) / float(len(windows_folded))

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


def _candidate_family_v1(candidate_bpm: int, base_bpm: int, *, tol_bpm: int) -> str:
    """
    Classify candidate tempo relative to a base tempo.

    Families:
      - base: ~base
      - double: ~2x base
      - half: ~0.5x base
      - triplet: ~2/3 base
      - dotted: ~3/2 base
    """
    tol = max(0, int(tol_bpm))
    base = int(base_bpm)
    cand = int(candidate_bpm)

    if abs(cand - base) <= tol:
        return "base"
    if abs(cand - (2 * base)) <= tol:
        return "double"
    if abs((2 * cand) - base) <= tol:
        return "half"

    trip = int(round(float(base) * (2.0 / 3.0)))
    if abs(cand - trip) <= tol:
        return "triplet"
    dotted = int(round(float(base) * 1.5))
    if abs(cand - dotted) <= tol:
        return "dotted"

    # v1 UI contract: no "other" family; default to base.
    return "base"


def _format_bpm_raw_v1(x: float) -> int | float:
    """
    Raw BPM is kept as a number, but we avoid long floats for determinism.
    - integers render as ints
    - non-integers render as 1 decimal place (e.g. 71.5)
    """
    xf = float(x)
    xr = round(xf)
    if abs(xf - float(xr)) <= 0.05:
        return int(xr)
    return float(round(xf, 1))


def _select_reportable_bpm_from_raw_v1(
    *,
    raw_bpm_exact: float,
    raw_bpm_rounded: int,
    raw_confidence: str,
    raw_stability: float,
    scored: list[tuple[int, float]],
    tol_bpm: int,
    config: EngineConfig,
) -> tuple[int | None, str, str, list[str]]:
    """
    Pure policy: decide UI-facing "reportable" BPM from raw BPM + evidence.

    Returns:
      (bpm_reportable_rounded_or_none, bpm_reportable_confidence, timefeel, reason_codes)
    """
    codes: list[str] = []

    # If raw itself is low confidence, reportable must be omitted (DO NOT LIE).
    if str(raw_confidence).lower() == "low":
        return None, "low", "unknown", ["omitted_low_confidence"]

    raw_exact = float(raw_bpm_exact)
    raw_round = int(raw_bpm_rounded)

    # Default behavior: prefer raw.
    reportable = int(round(raw_exact))
    reportable_conf = str(raw_confidence)
    timefeel = "normal"
    codes.append("prefer_raw")

    # Only consider 2x when raw is in the slower band.
    stab_min = float(config.tunables.bpm_reportable_raw_stability_min)
    raw_max = float(config.tunables.bpm_reportable_double_max_raw)
    dbl_min = int(config.tunables.bpm_reportable_double_min)
    dbl_max = int(config.tunables.bpm_reportable_double_max)
    runner_thresh = float(config.tunables.bpm_reportable_unrelated_competitor_threshold)
    cap = str(config.tunables.bpm_reportable_confidence_cap_without_direct_double_evidence)

    if raw_exact > raw_max:
        codes.append("capped_by_raw_max")
        return reportable, reportable_conf, timefeel, codes

    if raw_stability < stab_min:
        # Stable raw is a prerequisite for doubling.
        return reportable, reportable_conf, timefeel, codes

    dbl_exact = 2.0 * raw_exact
    dbl_round = int(round(dbl_exact))
    if dbl_round < dbl_min or dbl_round > dbl_max:
        return reportable, reportable_conf, timefeel, codes

    # Detect strong unrelated competitor (in a different tempo family).
    #
    # We treat +/-jitter and triplet/dotted as equivalent and ignore them for
    # "unrelated competitor" checks, but we do NOT ignore half/double ambiguity.
    top_score = float(scored[0][1]) if scored else 0.0
    runner_score = 0.0
    gap_tol = int(getattr(config.tunables, "bpm_gap_family_tolerance_bpm", max(2, int(tol_bpm))))
    for bpm_i, score in scored[1:]:
        if not _tempo_triplet_family_agrees(raw_round, int(bpm_i), tol_bpm=gap_tol):
            runner_score = float(score)
            break
    runner_frac = (
        (runner_score / top_score) if top_score > 0 else (1.0 if runner_score > 0 else 0.0)
    )
    if runner_frac >= runner_thresh:
        return None, "low", "unknown", ["ambiguous_runner_up", "omitted_low_confidence"]

    # Safe to prefer double-time as reportable.
    reportable = dbl_round
    timefeel = "double_time_preferred"
    codes = ["prefer_double_time_from_raw"]

    # Prefer emitting when within +/-1 of a candidate.
    if any(abs(int(b) - reportable) <= 1 for b, _ in scored):
        codes.append("prefer_emit_within_1")

    # Cap confidence to medium unless we have direct double evidence.
    #
    # We treat a non-zero score near the doubled tempo as direct evidence.
    direct_double = any(
        abs(int(b) - reportable) <= max(0, int(tol_bpm)) and float(s) > 0.0 for b, s in scored
    )
    if not direct_double and reportable_conf.lower() == "high":
        reportable_conf = cap

    return reportable, reportable_conf, timefeel, codes


def _weighted_mode_bpm_from_details(
    details: list[dict[str, Any]],
    *,
    bpm_key: str,
    score_key: str,
    lo_bpm: int,
    hi_bpm: int,
) -> tuple[int | None, float]:
    """
    Best-effort per-band "mode" tempo from window details.

    Returns (mode_bpm, stability_weighted) where stability_weighted is the
    fraction of total weight voting for the mode (0-1).
    """
    if not details:
        return None, 0.0

    weights: dict[int, float] = {}
    total_w = 0.0
    for d in details:
        try:
            bpm = float(d.get(bpm_key))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if bpm <= 0:
            continue
        bpm_f = _fold_into_range(bpm, lo=float(lo_bpm), hi=float(hi_bpm))
        bpm_i = int(round(bpm_f))
        if bpm_i < lo_bpm or bpm_i > hi_bpm:
            continue

        w = 1.0
        if score_key in d and d.get(score_key) is not None:
            try:
                w = float(d.get(score_key))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                w = 1.0
            # Clamp: details are "scores" but we do not assume their scale.
            if w < 0.0:
                w = 0.0
            if w > 1.0:
                w = 1.0

        weights[bpm_i] = weights.get(bpm_i, 0.0) + w
        total_w += w

    if not weights or total_w <= 0.0:
        return None, 0.0

    # Deterministic ties: choose smaller bpm.
    mode_bpm, mode_w = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return int(mode_bpm), float(mode_w / total_w)


def _weighted_top2_bpms_from_details(
    details: list[dict[str, Any]],
    *,
    bpm_key: str,
    score_key: str,
    lo_bpm: int,
    hi_bpm: int,
) -> tuple[int | None, float, int | None, float]:
    """
    Returns (top_bpm, top_frac, runnerup_bpm, runnerup_frac).

    Fractions are of total weight (0-1). Deterministic ties: smaller bpm wins.
    """
    if not details:
        return None, 0.0, None, 0.0

    weights: dict[int, float] = {}
    total_w = 0.0
    for d in details:
        try:
            bpm = float(d.get(bpm_key))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if bpm <= 0:
            continue
        bpm_i = int(round(_fold_into_range(bpm, lo=float(lo_bpm), hi=float(hi_bpm))))
        if bpm_i < lo_bpm or bpm_i > hi_bpm:
            continue

        w = 1.0
        if score_key in d and d.get(score_key) is not None:
            try:
                w = float(d.get(score_key))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                w = 1.0
            if w < 0.0:
                w = 0.0
            if w > 1.0:
                w = 1.0

        weights[bpm_i] = weights.get(bpm_i, 0.0) + w
        total_w += w

    if not weights or total_w <= 0.0:
        return None, 0.0, None, 0.0

    ranked = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    top_bpm, top_w = ranked[0]
    runner_bpm: int | None = None
    runner_w = 0.0
    if len(ranked) >= 2:
        runner_bpm, runner_w = ranked[1]
    return int(top_bpm), float(top_w / total_w), runner_bpm, float(runner_w / total_w)


def _tempo_family_agrees(a: int, b: int, *, tol_bpm: int) -> bool:
    tol = max(0, int(tol_bpm))
    if abs(a - b) <= tol:
        return True
    if abs(a - (2 * b)) <= tol:
        return True
    if abs((2 * a) - b) <= tol:
        return True
    # Triplet/dotted relationships (3/2 and 2/3).
    if abs(a - int(round(float(b) * 1.5))) <= tol:
        return True
    if abs(b - int(round(float(a) * 1.5))) <= tol:
        return True
    if abs(a - int(round(float(b) * (2.0 / 3.0)))) <= tol:
        return True
    if abs(b - int(round(float(a) * (2.0 / 3.0)))) <= tol:
        return True
    return False


def _tempo_triplet_family_agrees(a: int, b: int, *, tol_bpm: int) -> bool:
    """
    Tempo "family" equivalence for score-gap computation.

    We treat triplet/dotted (3/2 and 2/3) periodicities as equivalent evidence,
    because they frequently arise from production subdivisions (e.g. triplet hats)
    and should not be interpreted as a competing tempo family.

    We intentionally do *not* treat half/double as equivalent here, because that
    ambiguity is musically meaningful and should reduce confidence unless we
    have other evidence to disambiguate.
    """
    tol = max(0, int(tol_bpm))
    if abs(a - b) <= tol:
        return True
    if abs(a - int(round(float(b) * 1.5))) <= tol:
        return True
    if abs(b - int(round(float(a) * 1.5))) <= tol:
        return True
    if abs(a - int(round(float(b) * (2.0 / 3.0)))) <= tol:
        return True
    if abs(b - int(round(float(a) * (2.0 / 3.0)))) <= tol:
        return True
    return False


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

    windows_raw = _windows_from_ctx(ctx, config=config)
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

    tol_bpm = int(getattr(config.tunables, "bpm_window_match_tolerance_bpm", 1))
    triplet_beta = float(getattr(config.tunables, "bpm_triplet_support_beta", 0.8))
    triplet_min_direct = float(getattr(config.tunables, "bpm_triplet_support_min_direct", 0.05))
    scored = [
        (
            b,
            _score_candidate_from_windows(
                b,
                windows_folded,
                tol_bpm=tol_bpm,
                triplet_beta=triplet_beta,
                triplet_min_direct=triplet_min_direct,
            ),
        )
        for b in cand_bpms
    ]
    scored.sort(key=lambda t: (-t[1], t[0]))

    # Enforce minimum count.
    scored = scored[: max(5, top_n)]

    def direct_support(bpm: int) -> float:
        tol = max(0, tol_bpm)
        return sum(1 for w in windows_folded if abs(int(bpm) - int(w)) <= tol) / float(
            len(windows_folded)
        )

    # Triplet/dotted correction:
    # If the top periodicity is ~2/3 of a plausible tempo family, and we see at
    # least some direct evidence near the 3/2 tempo, prefer the 3/2 tempo.
    #
    # This specifically targets cases like 170 BPM with triplet hats -> strong
    # ~113 BPM autocorrelation, where 113 is not the intended reportable tempo.
    top0_bpm, top0_score = scored[0]
    promote_target = int(round(float(top0_bpm) * 1.5))
    promote_min_direct = float(getattr(config.tunables, "bpm_triplet_promote_min_direct", 0.05))
    promote_delta_max = float(getattr(config.tunables, "bpm_triplet_promote_score_delta_max", 0.08))

    if lo_bpm <= promote_target <= hi_bpm:
        tol = max(0, tol_bpm)
        promote_idx = None
        promote_score = None
        for i, (b, s) in enumerate(scored):
            if abs(int(b) - promote_target) <= tol:
                promote_idx = i
                promote_score = float(s)
                break

        if (
            promote_idx is not None
            and promote_idx > 0
            and direct_support(int(scored[promote_idx][0])) >= promote_min_direct
            and float(promote_score or 0.0) >= float(top0_score) - promote_delta_max
        ):
            promoted = scored.pop(promote_idx)
            scored.insert(0, promoted)

    s1 = scored[0][1]
    # If the runner jittered by +/-1 BPM, the top "two" candidates may be
    # effectively the same tempo. Compute the gap against the best *distinct*
    # competitor to avoid over-omitting (e.g. 119 vs 120), and to avoid
    # treating common triplet/dotted periodicities (~2/3) as separate evidence.
    s2 = 0.0
    gap_tol = int(getattr(config.tunables, "bpm_gap_family_tolerance_bpm", max(2, tol_bpm)))
    for b, s in scored[1:]:
        if not _tempo_triplet_family_agrees(int(scored[0][0]), int(b), tol_bpm=gap_tol):
            s2 = float(s)
            break
    gap = float(s1 - float(s2))

    # Stability: fraction of windows that match the top candidate within tolerance.
    #
    # Includes optional 2/3 tempo support when there is some direct evidence for
    # the top tempo (prevents "120 supports 180" artifacts).
    top_bpm = scored[0][0]
    tol = max(0, tol_bpm)
    direct = sum(1 for w in windows_folded if abs(w - top_bpm) <= tol)
    direct_support = direct / float(len(windows_folded))
    stability = direct_support
    if direct_support >= float(triplet_min_direct):
        two_thirds = int(round(float(top_bpm) * (2.0 / 3.0)))
        trip = sum(1 for w in windows_folded if abs(two_thirds - w) <= tol)
        stability = (direct + (float(triplet_beta) * float(trip))) / float(len(windows_folded))

    duration_seconds = float(getattr(ctx.audio, "duration_seconds", 0.0) or 0.0)
    confidence = _confidence_level(
        score_gap=gap, stability=stability, duration_seconds=duration_seconds, config=config
    )

    # Sanity check: if low-band and high-band disagree strongly, do not produce
    # a confident-wrong bpm.value. This uses signal evidence only and preserves
    # DO-NOT-LIE by downgrading to low confidence (value omitted).
    details = getattr(ctx, "bpm_hint_window_details", None)
    if details and isinstance(details, list):
        low_mode, low_stab = _weighted_mode_bpm_from_details(
            details,
            bpm_key="best_bpm",
            score_key="best_score",
            lo_bpm=lo_bpm,
            hi_bpm=hi_bpm,
        )
        high_mode, high_stab = _weighted_mode_bpm_from_details(
            details,
            bpm_key="high_best_bpm",
            score_key="high_best_score",
            lo_bpm=lo_bpm,
            hi_bpm=hi_bpm,
        )
        min_stab = float(getattr(config.tunables, "bpm_multiband_min_mode_stability", 0.65))
        family_tol = int(getattr(config.tunables, "bpm_multiband_family_tolerance_bpm", 2))

        if confidence in ("medium", "high"):
            if (
                low_mode is not None
                and high_mode is not None
                and low_stab >= min_stab
                and high_stab >= min_stab
                and not _tempo_family_agrees(low_mode, high_mode, tol_bpm=family_tol)
            ):
                confidence = "low"

            # If a band has a strong runner-up in a different tempo family, treat
            # the estimate as ambiguous (do not produce a confident-wrong value).
            runner_min = float(
                getattr(config.tunables, "bpm_multiband_runnerup_min_fraction", 0.30)
            )
            top_bpm = int(scored[0][0])
            gap_tol = int(getattr(config.tunables, "bpm_gap_family_tolerance_bpm", max(2, tol_bpm)))
            for bpm_key, score_key in (
                ("best_bpm", "best_score"),
                ("high_best_bpm", "high_best_score"),
            ):
                _, _, runner_bpm, runner_frac = _weighted_top2_bpms_from_details(
                    details,
                    bpm_key=bpm_key,
                    score_key=score_key,
                    lo_bpm=lo_bpm,
                    hi_bpm=hi_bpm,
                )
                if runner_bpm is None:
                    continue
                if runner_frac < runner_min:
                    continue
                # Ignore triplet/dotted equivalence; treat half/double as meaningful ambiguity.
                if _tempo_triplet_family_agrees(top_bpm, int(runner_bpm), tol_bpm=gap_tol):
                    continue
                confidence = "low"
                break

        # Half/double ambiguity evidence: if per-window decoding reports that
        # the half-lag (double-tempo) correlation is often close to the best lag,
        # do not force a single value.
        #
        # This avoids "confident-wrong" half/double picks on patterns where both
        # interpretations are plausible.
        ratio_min = float(getattr(config.tunables, "bpm_double_ratio_ambiguous_min", 0.45))
        frac_min = float(getattr(config.tunables, "bpm_double_ratio_ambiguous_min_fraction", 0.60))
        n = 0
        n_amb = 0
        for d in details:
            if not isinstance(d, dict):
                continue
            for k in ("double_ratio", "high_double_ratio"):
                v = d.get(k)
                if v is None:
                    continue
                try:
                    r = float(v)
                except (TypeError, ValueError):
                    continue
                n += 1
                if r >= ratio_min:
                    n_amb += 1
        if n and (n_amb / float(n)) >= frac_min:
            confidence = "low"

    raw_confidence = confidence

    # Compute a raw tempo estimate (exact) even if the final reportable value is omitted.
    raw_supporting = [w for w in windows_folded_f if int(round(w)) == int(top_bpm)]
    raw_exact = (
        sum(raw_supporting) / float(len(raw_supporting)) if raw_supporting else float(int(top_bpm))
    )

    (
        bpm_reportable,
        bpm_reportable_confidence,
        timefeel,
        reason_codes,
    ) = _select_reportable_bpm_from_raw_v1(
        raw_bpm_exact=float(raw_exact),
        raw_bpm_rounded=int(top_bpm),
        raw_confidence=str(raw_confidence),
        raw_stability=float(stability),
        scored=[(int(b), float(s)) for b, s in scored],
        tol_bpm=int(tol_bpm),
        config=config,
    )

    # Back-compat: top-level bpm.confidence/value reflect the reportable selection.
    confidence = str(bpm_reportable_confidence)

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
        # Advanced UI policy outputs (free/pro only; guests are stripped in packaging).
        "bpm_raw": _format_bpm_raw_v1(float(raw_exact)),
        "bpm_raw_confidence": str(raw_confidence),
        "bpm_reportable": int(bpm_reportable) if bpm_reportable is not None else None,
        "bpm_reportable_confidence": str(bpm_reportable_confidence),
        "timefeel": str(timefeel),
        "bpm_reason_codes": list(reason_codes),
    }

    # Structured candidates for UI (top 5).
    base_for_family = int(bpm_reportable) if bpm_reportable is not None else int(top_bpm)
    out["bpm_candidates"] = [
        {
            "candidate_bpm": int(b),
            "candidate_family": _candidate_family_v1(int(b), base_for_family, tol_bpm=1),
            "candidate_score": float(round(float(s), 4)),
        }
        for b, s in scored[:5]
    ]

    if confidence != "low" and bpm_reportable is not None:
        # bpm.value aligns with bpm_reportable (UI-facing).
        factor = 1.0
        if timefeel == "double_time_preferred":
            factor = 2.0
        elif timefeel == "half_time_preferred":
            factor = 0.5
        exact = float(raw_exact) * factor
        out["value"] = {"value_exact": float(exact), "value_rounded": int(bpm_reportable)}

    return out
