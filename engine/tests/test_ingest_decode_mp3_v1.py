from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import pytest

from engine.core.errors import EngineError
from engine.ingest.ingest_v1 import decode_input_path_v1


def _write_tiny_wav(path: Path) -> None:
    # Minimal valid WAV for stdlib wave reader (metadata-only ingest).
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(44100)
        wf.writeframes(b"\x00\x00" * 44100)  # 1 second (mono-equivalent frames)


def test_decode_mp3_requires_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "x.mp3"
    p.write_bytes(b"not really an mp3")

    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)

    with pytest.raises(EngineError) as excinfo:
        decode_input_path_v1(p)

    err = excinfo.value
    assert err.code == "UNSUPPORTED_INPUT"
    assert "ffmpeg" in err.message.lower()
    assert (err.context or {}).get("stage") == "decode"


def test_decode_mp3_ffmpeg_failure_raises_invalid_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "x.mp3"
    p.write_bytes(b"not really an mp3")

    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: "/opt/homebrew/bin/ffmpeg")

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["ffmpeg"], returncode=1, stdout="", stderr="decode failed"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(EngineError) as excinfo:
        decode_input_path_v1(p)

    err = excinfo.value
    assert err.code == "INVALID_INPUT"
    ctx = err.context or {}
    assert ctx.get("stage") == "decode"
    assert "stderr_snippet" in ctx


def test_decode_mp3_success_uses_temp_wav_and_preserves_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "x.mp3"
    p.write_bytes(b"not really an mp3")

    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: "/opt/homebrew/bin/ffmpeg")

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        out_wav = Path(args[-1])
        _write_tiny_wav(out_wav)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    audio = decode_input_path_v1(p)
    assert audio.format == "mp3"
    assert audio.codec == "mp3"
    assert audio.container == "mp3"
    assert audio.channels == 2
    assert audio.sample_rate_hz == 44100
    assert audio.duration_seconds > 0
