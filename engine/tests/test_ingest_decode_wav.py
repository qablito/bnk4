from __future__ import annotations

import wave
from pathlib import Path

from engine.ingest.decode_wav_v1 import decode_wav_v1


def _write_silence_wav(path: Path, *, sr: int = 44100, channels: int = 2, seconds: float = 1.0) -> None:
    nframes = int(sr * seconds)
    # 16-bit PCM silence
    sampwidth = 2
    silence_frame = (b"\x00\x00" * channels)
    data = silence_frame * nframes

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sr)
        wf.writeframes(data)


def test_decode_wav_v1_reads_basic_metadata(tmp_path: Path):
    wav_path = tmp_path / "silence.wav"
    _write_silence_wav(wav_path, sr=44100, channels=2, seconds=1.0)

    decoded = decode_wav_v1(wav_path)
    assert decoded.format == "wav"
    assert decoded.sample_rate_hz == 44100
    assert decoded.channels == 2
    assert 0.99 <= decoded.duration_seconds <= 1.01


def test_decode_wav_v1_enforces_max_seconds(tmp_path: Path):
    wav_path = tmp_path / "silence.wav"
    _write_silence_wav(wav_path, sr=44100, channels=1, seconds=1.0)

    try:
        decode_wav_v1(wav_path, max_seconds=0.5)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "max_seconds" in str(exc)