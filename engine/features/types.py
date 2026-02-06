# engine/features/types.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    bpm_hint_exact: Optional[float] = None
    key_mode_hint: Optional[str] = None  # e.g. "F# minor"