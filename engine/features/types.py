# engine/features/types.py
from __future__ import annotations

from dataclasses import dataclass

from engine.preprocess.preprocess_v1 import PreprocessedAudio


@dataclass(frozen=True)
class FeatureContext:
    """
    v1: no PCM. Only metadata plus placeholders for future feature vectors.
    """

    audio: PreprocessedAudio
    # Placeholder knobs to simulate analyzability in stubs/tests
    has_rhythm_evidence: bool = True
    has_tonal_evidence: bool = True

    # Optional “hints” to make deterministic tests possible
    bpm_hint_exact: float | None = None
    # Window-level tempo hints (for candidate + stability tests). Values are in BPM.
    bpm_hint_windows: list[float] | None = None
    key_mode_hint: str | None = None  # e.g. "F# minor"
    # Window-level key/mode hints (for candidate + stability tests). Values are like "F# minor".
    key_mode_hint_windows: list[str] | None = None
