# engine/preprocess/preprocess_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engine.core.config import EngineConfig
from engine.ingest.types import DecodedAudio


ChannelLayout = Literal["mono", "stereo"]


@dataclass(frozen=True)
class PreprocessedAudio:
    """
    v1 stub: no PCM is stored. This carries only validated/canonical metadata and
    prepares the pipeline for real preprocessing in a later step.
    """
    internal_sample_rate_hz: int
    channels: int
    duration_seconds: float
    layout: ChannelLayout


def preprocess_v1(audio: DecodedAudio, *, config: EngineConfig) -> PreprocessedAudio:
    """
    v1 behavior:
      - Validate minimal invariants (channels, duration, sample rate presence).
      - Canonicalize layout (mono/stereo).
      - Record internal target sample rate (no resample performed yet).
    """
    if audio.channels not in (1, 2):
        raise ValueError(f"unsupported channels: {audio.channels} (expected 1 or 2)")

    if audio.duration_seconds <= 0:
        raise ValueError(f"invalid duration_seconds: {audio.duration_seconds}")

    # v1 decision: internal analysis sample rate is fixed by tunables
    internal_sr = config.tunables.INTERNAL_SAMPLE_RATE_HZ

    layout: ChannelLayout = "mono" if audio.channels == 1 else "stereo"

    return PreprocessedAudio(
        internal_sample_rate_hz=internal_sr,
        channels=audio.channels,
        duration_seconds=float(audio.duration_seconds),
        layout=layout,
    )