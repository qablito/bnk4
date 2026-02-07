"""Types for evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Fixture:
    """Ground truth fixture for evaluation."""

    path: str
    bpm_gt: float | None
    key_gt: str | None  # e.g., "C", "C#", "D", etc.
    mode_gt: str | None  # "major" or "minor"
    flags: set[str]
    notes: str
    # Extra columns preserved as raw dict
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def is_bpm_strict(self) -> bool:
        return "bpm_strict" in self.flags

    @property
    def is_key_strict(self) -> bool:
        return "key_strict" in self.flags

    @property
    def is_ambiguous(self) -> bool:
        return "ambiguous" in self.flags

    @property
    def is_short_audio(self) -> bool:
        return "short_audio" in self.flags

    @property
    def is_double_time_preferred(self) -> bool:
        return "double_time_preferred" in self.flags


@dataclass
class PredictionResult:
    """Result from running analysis on a fixture."""

    fixture: Fixture
    success: bool
    error: str | None
    output: dict[str, Any] | None
    skipped: bool = False
    skip_reason: str | None = None

    # Extracted BPM predictions
    bpm_value_rounded: int | None = None
    bpm_value_exact: float | None = None
    bpm_candidates: list[dict[str, Any]] | None = None
    bpm_omitted: bool = True

    # Extracted key/mode predictions (for future use)
    key_value: str | None = None
    mode_value: str | None = None
    key_mode_omitted: bool = True


@dataclass
class BpmError:
    """BPM prediction error detail."""

    path: str
    bpm_gt: float
    bpm_pred: int | None
    abs_error: float
    candidates: list[int] | None
    notes: str


@dataclass
class EvalMetrics:
    """Evaluation metrics."""

    # Overall stats
    total_fixtures: int
    successful_runs: int
    failed_runs: int
    skipped_runs: int

    # BPM metrics (only bpm_strict fixtures)
    bpm_n_total_strict: int
    bpm_n_predicted: int
    bpm_n_omitted: int
    bpm_mae: float | None  # Mean Absolute Error
    bpm_omit_rate: float | None

    # Top errors
    top_bpm_errors: list[BpmError]

    # Key/mode metrics (for future)
    key_n_total_strict: int = 0
    key_n_predicted: int = 0
    key_n_omitted: int = 0
    key_accuracy: float | None = None
    key_omit_rate: float | None = None
