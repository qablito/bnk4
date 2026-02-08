from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.types import FeatureContext
from engine.preprocess.preprocess_v1 import PreprocessedAudio


def _ctx(*, duration_seconds: float, windows: list[float]) -> FeatureContext:
    pre = PreprocessedAudio(
        internal_sample_rate_hz=44100,
        channels=2,
        duration_seconds=duration_seconds,
        layout="stereo",
    )
    return FeatureContext(audio=pre, has_rhythm_evidence=True, bpm_hint_windows=windows)


def test_triplet_periodicity_promotes_to_3_over_2_when_direct_evidence_exists() -> None:
    """
    Triplet-heavy patterns can create a strong ~2/3 tempo periodicity (e.g. 102)
    even when the intended tempo is ~3/2 that (e.g. 153).

    If we see *some* direct evidence near 3/2, prefer the 3/2 tempo rather than
    omitting or returning the 2/3 periodicity.
    """
    cfg = EngineConfig()
    out = extract_bpm_v1(
        _ctx(duration_seconds=60.0, windows=([102.0] * 30) + ([154.0] * 6)), config=cfg
    )
    assert out is not None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("value", {}).get("value_rounded") in (153, 154)


def test_triplet_support_does_not_invent_3_over_2_without_direct_evidence() -> None:
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[120.0] * 12), config=cfg)
    assert out is not None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("value", {}).get("value_rounded") == 120
