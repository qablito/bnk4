from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features.key_mode_v1 import extract_key_mode_v1
from engine.features.types import FeatureContext
from engine.ingest.types import DecodedAudio
from engine.pipeline.run import run_analysis_v1
from engine.preprocess.preprocess_v1 import PreprocessedAudio


def _ctx(*, duration_seconds: float, windows: list[str]) -> FeatureContext:
    pre = PreprocessedAudio(
        internal_sample_rate_hz=44100,
        channels=2,
        duration_seconds=duration_seconds,
        layout="stereo",
    )
    return FeatureContext(
        audio=pre,
        has_tonal_evidence=True,
        key_mode_hint_windows=windows,
    )


def test_weak_harmonic_content_is_low_confidence_and_omits_value():
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(duration_seconds=60.0, windows=["F# minor", "A major", "C major", "E minor"]),
        config=cfg,
    )
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out
    assert isinstance(out.get("candidates"), list)
    assert len(out["candidates"]) >= 2


def test_multiple_keys_score_similarly_omits_value():
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(duration_seconds=60.0, windows=["F# minor", "A major", "F# minor", "A major"]),
        config=cfg,
    )
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out


def test_short_audio_is_low_confidence_and_omits_value_even_if_stable():
    cfg = EngineConfig()
    out = extract_key_mode_v1(_ctx(duration_seconds=3.0, windows=["F# minor"] * 4), config=cfg)
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out


def test_stable_key_returns_value_when_confident():
    cfg = EngineConfig()
    out = extract_key_mode_v1(_ctx(duration_seconds=60.0, windows=["F# minor"] * 8), config=cfg)
    assert out is not None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("value") == "F# minor"


def test_guest_gating_strips_candidate_metadata_and_confidence():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=30.0)
    out = run_analysis_v1(
        audio,
        "guest",
        config=EngineConfig(),
        _test_overrides={"key_mode_hint_windows": ["F# minor"] * 8},
    )

    km = out["metrics"]["key_mode"]
    assert "confidence" not in km

    for c in km.get("candidates", []):
        assert set(c.keys()) <= {"value", "rank"}
