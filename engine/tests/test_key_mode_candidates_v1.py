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
    assert out.get("value") is None
    assert out.get("mode") is None
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
    assert out.get("value") is None
    assert out.get("mode") is None
    assert out.get("reason_codes") == ["omitted_ambiguous_runnerup", "omitted_low_confidence"]


def test_short_audio_stable_can_emit_with_medium_confidence_when_not_ambiguous():
    cfg = EngineConfig()
    out = extract_key_mode_v1(_ctx(duration_seconds=3.0, windows=["F# minor"] * 4), config=cfg)
    assert out is not None
    assert out.get("confidence") == "medium"
    assert out.get("value") == "F#"
    assert out.get("mode") == "minor"
    assert out.get("reason_codes") == ["emit_consistent_weak_evidence"]


def test_short_audio_mostly_stable_emits_with_medium_confidence():
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(duration_seconds=3.0, windows=["F# minor"] * 3 + ["A major"]),
        config=cfg,
    )
    assert out is not None
    assert out.get("confidence") == "medium"
    assert out.get("value") == "F#"
    assert out.get("mode") is None
    assert out.get("reason_codes") == [
        "mode_withheld_insufficient_evidence",
        "emit_consistent_weak_evidence",
    ]


def test_key_emits_when_mode_is_ambiguous():
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(
            duration_seconds=60.0,
            windows=["A major"] * 3 + ["A minor"] * 2,
        ),
        config=cfg,
    )
    assert out is not None
    assert out.get("value") == "A"
    assert out.get("mode") is None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("reason_codes") == [
        "mode_withheld_insufficient_evidence",
        "emit_confident",
    ]


def test_pair_strong_emits_key_and_mode():
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(duration_seconds=60.0, windows=["A major"] * 4),
        config=cfg,
    )
    assert out is not None
    assert out.get("value") == "A"
    assert out.get("mode") == "major"
    assert out.get("confidence") in ("medium", "high")
    assert out.get("reason_codes") == ["emit_confident"]


def test_key_aggregate_wins_but_top_pair_is_different_key():
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(
            duration_seconds=60.0,
            windows=["A major"] * 4 + ["A minor"] * 4 + ["B major"] * 5,
        ),
        config=cfg,
    )
    assert out is not None
    assert out.get("value") == "A"
    assert out.get("mode") is None
    assert out.get("reason_codes") == [
        "mode_withheld_insufficient_evidence",
        "emit_confident",
    ]
    candidates = out.get("candidates") or []
    assert candidates and candidates[0].get("key") == "A"
    assert candidates[0].get("mode") is None


def test_too_short_audio_omits_even_if_stable():
    cfg = EngineConfig()
    out = extract_key_mode_v1(_ctx(duration_seconds=1.0, windows=["F# minor"] * 4), config=cfg)
    assert out is not None
    assert out.get("confidence") == "low"
    assert out.get("value") is None
    assert out.get("mode") is None


def test_stable_key_returns_value_when_confident():
    cfg = EngineConfig()
    out = extract_key_mode_v1(_ctx(duration_seconds=60.0, windows=["F# minor"] * 8), config=cfg)
    assert out is not None
    assert out.get("confidence") in ("medium", "high")
    assert out.get("value") == "F#"
    assert out.get("mode") == "minor"
    assert out.get("reason_codes") == ["emit_confident"]


def test_reason_codes_order_is_deterministic() -> None:
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(duration_seconds=3.0, windows=["F# minor", "A major", "F# minor", "A major"]),
        config=cfg,
    )
    assert out is not None
    assert out.get("reason_codes") == ["omitted_ambiguous_runnerup", "omitted_low_confidence"]


def test_candidates_order_is_deterministic_on_ties() -> None:
    cfg = EngineConfig()
    out = extract_key_mode_v1(
        _ctx(duration_seconds=60.0, windows=["F# minor", "A minor", "F# minor", "A minor"]),
        config=cfg,
    )
    assert out is not None
    cands = out.get("candidates") or []
    assert cands[:2] == [
        {"key": "F#", "mode": "minor", "score": 0.5, "family": "direct", "rank": 1},
        {"key": "A", "mode": "minor", "score": 0.5, "family": "direct", "rank": 2},
    ]


def test_guest_gating_strips_candidate_metadata_and_confidence():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=30.0)
    out = run_analysis_v1(
        audio,
        "guest",
        config=EngineConfig(),
        _test_overrides={"key_mode_hint_windows": ["F# minor"] * 8},
    )

    km = out["metrics"]["key"]
    assert "confidence" not in km
    assert "reason_codes" not in km
    assert "candidates" not in km

    # Back-compat alias should not leak advanced either.
    km_legacy = out["metrics"]["key_mode"]
    assert "confidence" not in km_legacy
    assert "reason_codes" not in km_legacy
    assert "candidates" not in km_legacy


def test_free_gating_keeps_advanced_key_fields():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=30.0)
    out = run_analysis_v1(
        audio,
        "free",
        config=EngineConfig(),
        _test_overrides={"key_mode_hint_windows": ["F# minor"] * 8},
    )

    km = out["metrics"]["key"]
    assert km.get("value") == "F#"
    assert km.get("mode") == "minor"
    assert km.get("confidence") in ("medium", "high")
    assert km.get("reason_codes") == ["emit_confident"]
    assert isinstance(km.get("candidates"), list) and km["candidates"]
