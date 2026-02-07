from __future__ import annotations

from engine.core.config import EngineConfig
from engine.ingest.types import DecodedAudio
from engine.packaging.package_output_v1 import package_output_v1
from engine.pipeline.run import run_analysis_v1


def test_guest_events_empty_and_bpm_exact_removed():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(
        audio,
        "guest",
        config=EngineConfig(),
        _test_overrides={
            "has_rhythm_evidence": True,
            "has_tonal_evidence": True,
            "bpm_hint_exact": 69.8,
            "key_mode_hint": "F# minor",
        },
    )
    assert out["events"] == {}

    bpm = out.get("metrics", {}).get("bpm")
    if bpm is not None:
        assert "value" in bpm
        assert "value_rounded" in bpm["value"]
        assert "value_exact" not in bpm["value"]


def test_free_events_categorized_present():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "free", config=EngineConfig())
    assert isinstance(out.get("events"), dict)
    for k in ("clipping", "stereo", "tonality", "noise"):
        assert k in out["events"]


def test_locked_preview_empty_is_omitted():
    synthetic = {
        "metrics": {
            "grid": {"locked": True, "unlock_hint": "x", "preview": {}},
        },
    }
    packaged = package_output_v1(synthetic, role="free")
    assert "preview" not in packaged["metrics"]["grid"]
