from __future__ import annotations

import wave
from pathlib import Path
from typing import Optional

from engine.ingest.types import DecodedAudio


def decode_wav_v1(path: str | Path, *, max_seconds: Optional[float] = None) -> DecodedAudio:
    """
    Decode WAV metadata using stdlib `wave` (v1: metadata-only).

    Returns a DecodedAudio object without PCM payload. This is intentionally light:
    - No numpy
    - No librosa
    - No external decoders

    Raises:
      - FileNotFoundError if path does not exist
      - ValueError for invalid/unsupported WAV or invalid parameters
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if max_seconds is not None and max_seconds <= 0:
        raise ValueError("max_seconds must be > 0 when provided")

    try:
        with wave.open(str(p), "rb") as wf:
            channels = int(wf.getnchannels())
            sample_rate = int(wf.getframerate())
            frames = int(wf.getnframes())

            if channels <= 0:
                raise ValueError("invalid WAV: channels must be > 0")
            if sample_rate <= 0:
                raise ValueError("invalid WAV: sample_rate_hz must be > 0")
            if frames < 0:
                raise ValueError("invalid WAV: frames must be >= 0")

            duration = frames / float(sample_rate) if sample_rate else 0.0

            # Optional limiter (ingest safeguard)
            if max_seconds is not None and duration > max_seconds:
                raise ValueError(f"WAV duration exceeds max_seconds ({duration:.3f}s > {max_seconds:.3f}s)")

            return DecodedAudio(
                sample_rate_hz=sample_rate,
                channels=channels,
                duration_seconds=float(duration),
                format="wav",
            )
    except wave.Error as exc:
        # Covers invalid header / unsupported codec inside WAV
        raise ValueError(f"invalid or unsupported WAV: {exc}") from exc