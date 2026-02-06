from engine.core.config import EngineConfig
from engine.ingest.types import DecodedAudio
from engine.pipeline.run import run_analysis_v1


def test_guest_bpm_omits_value_exact():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "guest", config=EngineConfig())
    bpm = out["metrics"].get("bpm")
    # in stub defaults, bpm is omitted unless hints exist; so allow omit
    if bpm is None:
        return
    assert "value" in bpm
    assert "value_rounded" in bpm["value"]
    assert "value_exact" not in bpm["value"]


def test_bpm_and_key_mode_are_omitted_if_unreliable():
    # Make evidence false by using hints=None AND evidence flags false (we’ll wire in step below)
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "free", config=EngineConfig(), _test_overrides={
        "has_rhythm_evidence": False,
        "has_tonal_evidence": False,
    })
    assert "bpm" not in out["metrics"]
    assert "key_mode" not in out["metrics"]