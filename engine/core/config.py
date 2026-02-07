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
