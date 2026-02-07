from __future__ import annotations

import wave
from pathlib import Path

from engine.contracts.analysis_output import validate_analysis_output_v1
from engine.core.config import EngineConfig
from engine.pipeline.run import run_analysis_v1


def _write_silence_wav(
    path: Path, *, sr: int = 44100, seconds: float = 1.0, channels: int = 2
) -> None:
    nframes = int(sr * seconds)
    sampwidth = 2  # 16-bit
    silence_frame = (b"\x00\x00") * channels  # one frame (all channels)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sr)
        wf.writeframes(silence_frame * nframes)


def test_run_analysis_v1_accepts_input_path_kw(tmp_path: Path):
    wav = tmp_path / "x.wav"
    _write_silence_wav(wav)

    out = run_analysis_v1(role="guest", input_path=str(wav), config=EngineConfig())
    validate_analysis_output_v1(out)

    assert out["track"]["format"] == "wav"
    assert out["track"]["sample_rate_hz"] == 44100
    assert out["role"] == "guest"
    assert out["events"] == {}


def test_run_analysis_v1_accepts_positional_path(tmp_path: Path):
    wav = tmp_path / "x.wav"
    _write_silence_wav(wav)

    out = run_analysis_v1(str(wav), "free", config=EngineConfig())
    validate_analysis_output_v1(out)

    assert out["track"]["format"] == "wav"
    assert out["role"] == "free"
    assert "events" in out
