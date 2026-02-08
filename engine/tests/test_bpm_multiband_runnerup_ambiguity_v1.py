from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.types import FeatureContext
from engine.preprocess.preprocess_v1 import PreprocessedAudio


def _ctx(*, duration_seconds: float, details: list[dict]) -> FeatureContext:
    pre = PreprocessedAudio(
        internal_sample_rate_hz=44100,
        channels=2,
        duration_seconds=duration_seconds,
        layout="stereo",
    )
    return FeatureContext(
        audio=pre,
        has_rhythm_evidence=True,
        bpm_hint_windows=None,
        bpm_hint_window_details=details,
    )


def test_strong_band_runnerup_downgrades_confidence_to_omit_value() -> None:
    """
    If a band has a strong runner-up that is not a triplet/dotted equivalence
    of the selected tempo, treat the estimate as ambiguous and omit bpm.value.
    """
    cfg = EngineConfig()
    details = [
        {
            "best_bpm": 122.0,
            "best_score": 0.9,
            "high_best_bpm": 122.0,
            "high_best_score": 0.9,
        }
        for _ in range(25)
    ] + [
        {
            "best_bpm": 92.0,
            "best_score": 0.9,
            "high_best_bpm": 92.0,
            "high_best_score": 0.9,
        }
        for _ in range(15)
    ]
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, details=details), config=cfg)
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out
    cands = [c["value"]["value_rounded"] for c in out.get("candidates", [])]
    assert 122 in cands
    assert 92 in cands
