# engine/core/config.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EngineV1Tunables:
    """
    Engine v1 tunables (normative defaults).

    These are *behavioral thresholds* and consolidation parameters that must
    remain stable unless we bump the spec. Values are derived from ANALYSIS_ENGINE_V1.md.
    """

    # Internal processing
    INTERNAL_SAMPLE_RATE_HZ: int = 44100

    # Omit thresholds (global, applies to all roles)
    bpm_min_confidence_omit: float = 0.35
    key_mode_min_confidence_omit: float = 0.45

    # Tempo candidates (half/double)
    tempo_half_double_delta_max: float = 0.08

    # Grid thresholds
    grid_min_confidence_omit: float = 0.25
    grid_min_confidence_minimally_usable: float = 0.45
    grid_guest_preview_min_confidence: float = 0.60

    # Event consolidation (Pro)
    merge_gap_seconds: float = 0.10
    min_range_seconds: float = 0.02

    # -----------------
    # BPM v1 Tunables
    # -----------------
    bpm_normalize_min: int = 60
    bpm_normalize_max: int = 200
    bpm_candidates_top_n: int = 5
    bpm_window_match_tolerance_bpm: int = 1

    bpm_gap_min_medium: float = 0.12
    bpm_gap_min_high: float = 0.20
    bpm_stability_min_medium: float = 0.60
    bpm_stability_min_high: float = 0.75
    bpm_min_duration_seconds_medium: float = 4.0
    bpm_min_duration_seconds_high: float = 6.0

    bpm_triplet_support_beta: float = 0.80
    bpm_triplet_support_min_direct: float = 0.05
    bpm_triplet_promote_min_direct: float = 0.05
    bpm_triplet_promote_score_delta_max: float = 0.08

    bpm_gap_family_tolerance_bpm: int = 2
    bpm_multiband_min_mode_stability: float = 0.65
    bpm_multiband_family_tolerance_bpm: int = 2

    bpm_double_ratio_ambiguous_min: float = 0.45
    bpm_double_ratio_ambiguous_min_fraction: float = 0.60

    # Minimum per-window hint "score" to include details in scoring. When unset,
    # low-quality periodicities can dominate the histogram and cause confident-wrong.
    bpm_hint_window_min_score: float = 0.20

    # -----------------------------
    # BPM Reportable Policy (v1)
    # -----------------------------
    # Policy: reportable BPM may prefer 2x raw for DJ-facing UX in double-time genres,
    # but only when raw is stable and there is no strong unrelated competitor.
    bpm_reportable_raw_stability_min: float = 0.75
    bpm_reportable_double_max_raw: int = 95
    bpm_reportable_double_min: int = 120
    bpm_reportable_double_max: int = 190
    bpm_reportable_unrelated_competitor_threshold: float = 0.30
    bpm_reportable_require_direct_double_evidence_for_flip: bool = True
    bpm_reportable_confidence_cap_without_direct_double_evidence: str = "medium"
    bpm_reportable_direct_double_min_score: float = 0.12
    bpm_reportable_direct_double_min_support: float = 0.08


DEFAULT_TUNABLES_V1 = EngineV1Tunables()


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass(frozen=True)
class EngineConfig:
    """
    Minimal config wrapper for pipeline wiring.

    We keep a stable name (`EngineConfig`) because pipeline/tests import it.
    """

    tunables: EngineV1Tunables = field(default_factory=lambda: DEFAULT_TUNABLES_V1)
