from engine.core.config import EngineConfig
from engine.ingest.types import DecodedAudio
from engine.pipeline.run import run_analysis_v1
from engine.contracts.analysis_output import validate_analysis_output_v1

def test_run_analysis_v1_guest_passes_contract():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "guest", config=EngineConfig())
    validate_analysis_output_v1(out)

def test_run_analysis_v1_free_passes_contract():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "free", config=EngineConfig())
    validate_analysis_output_v1(out)

def test_run_analysis_v1_pro_passes_contract():
    audio = DecodedAudio(sample_rate_hz=44100, channels=2, duration_seconds=10.0)
    out = run_analysis_v1(audio, "pro", config=EngineConfig())
    validate_analysis_output_v1(out)
