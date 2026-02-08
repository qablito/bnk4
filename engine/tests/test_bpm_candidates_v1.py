from __future__ import annotations

from engine.core.config import EngineConfig
from engine.features.bpm_v1 import extract_bpm_v1
from engine.features.types import FeatureContext
from engine.ingest.types import DecodedAudio
from engine.pipeline.run import run_analysis_v1
from engine.preprocess.preprocess_v1 import PreprocessedAudio


def _ctx(*, duration_seconds: float, windows: list[float]) -> FeatureContext:
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
    )


def test_half_double_ambiguity_omits_value_but_returns_candidates():
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=60.0, windows=[70, 70, 140, 140]), config=cfg)
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out
    assert isinstance(out.get("candidates"), list)
    assert len(out["candidates"]) >= 5

    bpms = {c["value"]["value_rounded"] for c in out["candidates"]}
    assert 70 in bpms
    assert 140 in bpms


def test_stable_tempo_returns_value_when_confident():
    cfg = EngineConfig()
    out = extract_bpm_v1(
        _ctx(duration_seconds=60.0, windows=[140, 140, 140, 140, 140, 140]), config=cfg
    )
    assert out is not None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("value", {}).get("value_rounded") == 140
    assert len(out.get("candidates", [])) >= 5


def test_short_audio_is_low_confidence_and_omits_value():
    cfg = EngineConfig()
    out = extract_bpm_v1(_ctx(duration_seconds=3.0, windows=[140, 140, 140]), config=cfg)
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out
    assert len(out.get("candidates", [])) >= 5


def test_unstable_tempo_is_low_confidence_and_omits_value():
    cfg = EngineConfig()
    out = extract_bpm_v1(
        _ctx(duration_seconds=120.0, windows=[120, 130, 120, 130, 120, 130]), config=cfg
    )
    assert out is not None
    assert out.get("confidence") == "low"
    assert "value" not in out
    assert len(out.get("candidates", [])) >= 5


def test_nearby_windows_are_treated_as_stable_enough_to_return_value():
    """
    Real signals jitter by ~1 BPM between windows. v1 should not omit a value
    purely due to +/-1 rounding noise when the tempo family is consistent.
    """
    cfg = EngineConfig()
    out = extract_bpm_v1(
        _ctx(duration_seconds=60.0, windows=[118.9, 119.2, 120.1, 118.7, 119.8, 120.2]),
        config=cfg,
    )
    assert out is not None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("value", {}).get("value_rounded") in (119, 120, 118)
    assert len(out.get("candidates", [])) >= 5


def test_guest_gating_strips_candidate_metadata_and_value_exact():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=30.0)
    out = run_analysis_v1(
        audio,
        "guest",
        config=EngineConfig(),
        _test_overrides={"bpm_hint_windows": [140, 140, 140, 140, 140, 140]},
    )

    bpm = out["metrics"]["bpm"]
    assert bpm["value"] == {"value_rounded": 140}

    # Advanced policy fields must not leak to guest.
    for k in (
        "bpm_raw",
        "bpm_raw_confidence",
        "bpm_reportable",
        "bpm_reportable_confidence",
        "timefeel",
        "bpm_reason_codes",
        "bpm_candidates",
    ):
        assert k not in bpm

    # Candidates must not leak score/relation to guest.
    for c in bpm.get("candidates", []):
        assert set(c.keys()) <= {"value", "rank"}


def test_non_guest_bpm_advanced_payload_exposes_ui_fields():
    """
    Backend schema alignment for the UI Advanced BPM panel.

    The frontend is expected to map these exact keys into the advanced disclosure.
    """
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=30.0)
    out = run_analysis_v1(
        audio,
        "pro",
        config=EngineConfig(),
        _test_overrides={"bpm_hint_windows": [71.4] * 12},
    )

    bpm = out["metrics"]["bpm"]
    assert bpm["value"]["value_rounded"] == bpm["bpm_reportable"]
    assert bpm["bpm_raw"] == 71.4
    assert bpm["bpm_reportable"] == 71
    assert bpm["timefeel"] in (
        "normal",
        "double_time_preferred",
        "half_time_preferred",
        "unknown",
    )
    assert isinstance(bpm.get("bpm_reason_codes"), list)
    assert isinstance(bpm.get("bpm_candidates"), list)
    assert len(bpm["bpm_candidates"]) <= 5
    assert all(
        {"candidate_bpm", "candidate_family", "candidate_score"} <= set(row.keys())
        for row in bpm["bpm_candidates"]
    )
