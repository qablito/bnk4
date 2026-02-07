from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.ingest.types import AudioFormat, DecodedAudio


@dataclass(frozen=True)
class IngestLimits:
    max_bytes: int
    max_duration_seconds: float | None = None


def _guess_format_from_suffix(path: Path) -> AudioFormat:
    s = path.suffix.lower().lstrip(".")
    if s in ("wav", "mp3", "flac", "ogg"):
        return s  # type: ignore[return-value]
    return "unknown"


def ingest_v1(
    source: bytes | str | Path,
    *,
    limits: IngestLimits,
) -> DecodedAudio:
    """
    v1 ingest stub.
    - Validates byte size (when available).
    - Returns a DecodedAudio placeholder.
    Real decoding is deferred until we introduce audio deps.
    """

    if isinstance(source, (str, Path)):
        p = Path(source)
        # Size check (file exists) — purely best-effort
        if p.exists():
            size = p.stat().st_size
            if size > limits.max_bytes:
                raise ValueError(f"file too large: {size} > {limits.max_bytes}")
        fmt: AudioFormat = _guess_format_from_suffix(p)
    else:
        if len(source) > limits.max_bytes:
            raise ValueError(f"bytes too large: {len(source)} > {limits.max_bytes}")
        fmt = "unknown"

    # Placeholder audio: keep consistent defaults for tests/dev.
    # Real decoder will replace these with actual values.
    audio = DecodedAudio(
        sample_rate_hz=44100,
        channels=2,
        duration_seconds=0.0,
        format=fmt,
    )

    return audio
