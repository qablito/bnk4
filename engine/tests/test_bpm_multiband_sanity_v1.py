from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.types import FeatureContext
from engine.preprocess.preprocess_v1 import PreprocessedAudio


def _ctx(*, duration_seconds: float, windows: list[float], details: list[dict]) -> FeatureContext:
    pre = PreprocessedAudio(
        internal_sample_rate_hz=44100,
        channels=2,
        duration_seconds=duration_seconds,
        layout="stereo",
    )
    return FeatureContext(
        audio=pre,
        has_rhythm_evidence=True,
        bpm_hint_windows=windows,
        bpm_hint_window_details=details,
    )


def test_multiband_disagreement_downgrades_confidence_to_omit_value() -> None:
    """
    If the low-band and high-band estimators strongly disagree, we must not
    produce a confident-wrong bpm.value. Candidates can still be returned.
    """
    cfg = EngineConfig()
    ctx = _ctx(
        duration_seconds=60.0,
        windows=[102.0] * 12,  # stable but potentially wrong periodicity
        details=[
            {
                # Low-band
                "best_bpm": 102.0,
                "best_score": 0.9,
                # High-band disagrees
                "high_best_bpm": 140.0,
                "high_best_score": 0.9,
            }
            for _ in range(12)
        ],
    )
    out = extract_bpm_v1(ctx, config=cfg)
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out
    assert len(out.get("candidates", [])) >= 5


def test_low_score_details_are_filtered_out_before_scoring() -> None:
    """
    Window details can contain low-quality outliers (e.g. hat subdivisions)
    that should not dominate scoring.
    """
    cfg = EngineConfig()
    ctx = _ctx(
        duration_seconds=60.0,
        windows=[],
        details=(
            [
                {
                    "best_bpm": 140.0,
                    "best_score": 0.05,
                    "high_best_bpm": 140.0,
                    "high_best_score": 0.05,
                }
                for _ in range(9)
            ]
            + [
                {
                    "best_bpm": 80.0,
                    "best_score": 0.9,
                    "high_best_bpm": 80.0,
                    "high_best_score": 0.9,
                }
                for _ in range(3)
            ]
        ),
    )
    out = extract_bpm_v1(ctx, config=cfg)
    assert out is not None
    # Raw is ~80; without direct double evidence, reportable stays raw.
    assert out.get("bpm_raw") == 80
    assert out.get("bpm_reportable") == 80
    assert out.get("value", {}).get("value_rounded") == 80
