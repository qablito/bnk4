from __future__ import annotations

from pathlib import Path

from engine.ingest.decode_wav_v1 import decode_wav_v1
from engine.ingest.types import DecodedAudio


def decode_input_path_v1(path: Path) -> DecodedAudio:
    """
    v1 ingest dispatcher.

    v1 supports ONLY .wav via stdlib metadata-only decoding.
    This file exists to keep run_analysis_v1 clean and to prepare for v2 formats
    without changing the runner contract.

    Raises:
      - ValueError for unsupported extensions
      - Whatever decode_wav_v1 raises for invalid/unsupported WAV files
    """
    suffix = path.suffix.lower()

    if suffix == ".wav":
        return decode_wav_v1(path)

    raise ValueError("v1 input_path only supports .wav")