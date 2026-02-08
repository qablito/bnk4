"""Types for evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Fixture:
    """Ground truth fixture for evaluation."""

    path: str
    bpm_gt_raw: float | None
    bpm_gt_reportable: float | None
    key_gt: str | None  # e.g., "C", "C#", "D", etc.
    mode_gt: str | None  # "major" or "minor"
    flags: set[str]
    notes: str
    # Extra columns preserved as raw dict
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def bpm_gt(self) -> float | None:
        """
        Back-compat alias for the legacy single BPM ground truth.

        Historically this harness used a single `bpm_gt` column. We now split
        ground truth into raw (grid) and reportable (what a human would label).
        Defaulting to reportable preserves prior semantics.
        """
        return self.bpm_gt_reportable

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
    skip_reason_code: str | None = None

    # Structured diagnostics (safe-to-log). Populated on failed runs.
    failure: dict[str, Any] | None = None

    # Extracted BPM predictions
    bpm_value_rounded: int | None = None
    bpm_value_exact: float | None = None
    bpm_candidates: list[dict[str, Any]] | None = None
    bpm_omitted: bool = True

    # Extracted raw BPM (advanced; may be present even when reportable is omitted)
    bpm_raw_value_rounded: int | None = None
    bpm_raw_value_exact: float | None = None
    bpm_raw_omitted: bool = True
    # Deterministic policy trace from metrics.bpm.bpm_reason_codes.
    bpm_reason_codes: list[str] | None = None
    # Structured advanced candidates from metrics.bpm.bpm_candidates (family + score).
    bpm_candidates_structured: list[dict[str, Any]] | None = None

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
    kind: Literal["raw", "reportable"] = "reportable"


@dataclass
class BpmHalfDoubleConfusion:
    """
    Diagnostic record for half/double-time mismatches between raw and reportable GT.
    """

    path: str
    bpm_gt_raw: float
    bpm_gt_reportable: float
    bpm_pred: int
    relation: Literal["pred_matches_raw", "pred_matches_reportable"]
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

    # BPM metrics: reportable (what humans label)
    bpm_reportable_n_total_strict: int
    bpm_reportable_n_predicted: int
    bpm_reportable_n_omitted: int
    bpm_reportable_mae: float | None  # Mean Absolute Error
    bpm_reportable_omit_rate: float | None
    bpm_family_match_rate_reportable: float | None
    bpm_reportable_omit_reason_counts: dict[str, int]
    bpm_policy_flip_rate: float | None

    # BPM metrics: raw (grid / fundamental pulse)
    bpm_raw_n_total_strict: int
    bpm_raw_n_predicted: int
    bpm_raw_n_omitted: int
    bpm_raw_mae: float | None
    bpm_raw_omit_rate: float | None

    # Top errors per GT kind
    top_bpm_errors_reportable: list[BpmError]
    top_bpm_errors_raw: list[BpmError]

    # Half/double confusion stats (only when both GT kinds are present)
    bpm_half_double_confusion_count: int = 0
    bpm_half_double_confusions: list[BpmHalfDoubleConfusion] = field(default_factory=list)
    bpm_half_double_confusion_matrix: dict[str, int] = field(default_factory=dict)

    # Key/mode metrics (for future)
    key_n_total_strict: int = 0
    key_n_predicted: int = 0
    key_n_omitted: int = 0
    key_accuracy: float | None = None
    key_omit_rate: float | None = None
