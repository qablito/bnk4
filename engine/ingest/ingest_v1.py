from __future__ import annotations

from pathlib import Path

from engine.core.errors import EngineError
from engine.ingest.decode_wav_v1 import decode_wav_v1
from engine.ingest.types import DecodedAudio


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
            return decode_wav_v1(path)
        except Exception as exc:
            raise EngineError(
                code="INVALID_INPUT",
                message="Invalid input",
                context={"path": str(path), "reason": str(exc)},
            ) from exc

    raise EngineError(
        code="UNSUPPORTED_INPUT",
        message="Unsupported input format",
        context={"path": str(path), "suffix": suffix},
    )
