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
    codec: str | None = None
    container: str | None = None

    # Reserved for v2 / real decoding
    peak_dbfs: float | None = None

    # v1 derived hints (computed from PCM when available)
    bpm_hint_windows: list[float] | None = None
    # Optional per-window detail for half/double ambiguity (internal; not exposed to guests).
    bpm_hint_window_details: list[dict[str, float | None]] | None = None
