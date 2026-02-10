from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from engine.core.errors import EngineError
from engine.ingest.decode_wav_v1 import decode_wav_v1
from engine.ingest.types import DecodedAudio
from engine.preprocess.bpm_hint_windows_v1 import (
    compute_bpm_hint_window_details_from_wav_v1,
    compute_bpm_hint_windows_from_wav_v1,
)


def _stderr_snippet(s: str, *, limit: int = 400) -> str:
    t = (s or "").strip()
    if len(t) <= limit:
        return t
    return t[:limit] + "..."


def _decode_mp3_via_ffmpeg_v1(path: Path) -> DecodedAudio:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise EngineError(
            code="UNSUPPORTED_INPUT",
            message="ffmpeg is required to decode mp3",
            context={
                "stage": "decode",
                "path": str(path),
                "suffix": ".mp3",
                "dependency": "ffmpeg",
            },
        )

    # v1 ingest is metadata-only. We transcode to WAV because stdlib `wave`
    # cannot read mp3, and we avoid heavy Python deps.
    with tempfile.TemporaryDirectory(prefix="bnk_ingest_mp3_") as td:
        out_wav = Path(td) / "decoded.wav"
        cmd = [
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(path),
            "-vn",
            "-f",
            "wav",
            str(out_wav),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise EngineError(
                code="INVALID_INPUT",
                message="Failed to decode mp3",
                context={
                    "stage": "decode",
                    "path": str(path),
                    "suffix": ".mp3",
                    "ffmpeg_returncode": int(proc.returncode),
                    "stderr_snippet": _stderr_snippet(proc.stderr),
                },
            )

        try:
            wav_audio = decode_wav_v1(out_wav)
        except Exception as exc:
            raise EngineError(
                code="INVALID_INPUT",
                message="Invalid input",
                context={
                    "stage": "decode",
                    "path": str(path),
                    "suffix": ".mp3",
                    "reason": str(exc),
                },
            ) from exc

        try:
            bpm_details = compute_bpm_hint_window_details_from_wav_v1(out_wav)
            bpm_windows = compute_bpm_hint_windows_from_wav_v1(out_wav)
        except Exception:
            bpm_details = None
            bpm_windows = None

        # Preserve original input format for downstream reporting.
        return DecodedAudio(
            sample_rate_hz=int(wav_audio.sample_rate_hz),
            channels=int(wav_audio.channels),
            duration_seconds=float(wav_audio.duration_seconds),
            format="mp3",
            codec="mp3",
            container="mp3",
            bpm_hint_windows=bpm_windows,
            bpm_hint_window_details=bpm_details if bpm_details is not None else None,
        )


def decode_input_path_v1(path: Path) -> DecodedAudio:
    """
    v1 ingest dispatcher.

    v1 supports ONLY .wav via stdlib metadata-only decoding.
    This file exists to keep run_analysis_v1 clean and to prepare for v2 formats
    without changing the runner contract.

    Raises:
      - EngineError(UNSUPPORTED_INPUT) for unsupported extensions
      - EngineError(INVALID_INPUT) for invalid/unsupported WAV files
    """
    suffix = path.suffix.lower()

    if suffix == ".wav":
        try:
            wav_audio = decode_wav_v1(path)
        except Exception as exc:
            raise EngineError(
                code="INVALID_INPUT",
                message="Invalid input",
                context={
                    "stage": "decode",
                    "path": str(path),
                    "suffix": suffix,
                    "reason": str(exc),
                },
            ) from exc

        try:
            bpm_details = compute_bpm_hint_window_details_from_wav_v1(path)
            bpm_windows = compute_bpm_hint_windows_from_wav_v1(path)
        except Exception:
            bpm_details = None
            bpm_windows = None

        return DecodedAudio(
            sample_rate_hz=int(wav_audio.sample_rate_hz),
            channels=int(wav_audio.channels),
            duration_seconds=float(wav_audio.duration_seconds),
            format="wav",
            codec=wav_audio.codec,
            container=wav_audio.container,
            peak_dbfs=wav_audio.peak_dbfs,
            bpm_hint_windows=bpm_windows,
            bpm_hint_window_details=bpm_details if bpm_details is not None else None,
        )

    if suffix == ".mp3":
        return _decode_mp3_via_ffmpeg_v1(path)

    raise EngineError(
        code="UNSUPPORTED_INPUT",
        message="Unsupported input format",
        context={"stage": "decode", "path": str(path), "suffix": suffix},
    )
