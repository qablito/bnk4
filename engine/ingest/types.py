from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AudioFormat = Literal["wav", "mp3", "flac", "ogg", "unknown"]


@dataclass(frozen=True)
class DecodedAudio:
    """
    Canonical in-memory representation passed into the analysis pipeline.

    NOTE: v1 scaffolding does NOT store PCM arrays yet (no heavy deps).
    When decoding is implemented, this type may gain a `pcm` field or a
    handle to a memory-mapped buffer. Until then, keep it minimal.
    """

    sample_rate_hz: int
    channels: int
    duration_seconds: float
    format: AudioFormat = "unknown"

    # Reserved for v2 / real decoding
    peak_dbfs: float | None = None
