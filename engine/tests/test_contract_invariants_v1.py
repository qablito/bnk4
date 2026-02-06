from __future__ import annotations

import pytest

from engine.contracts.analysis_output import ContractViolation, validate_analysis_output_v1


def _base_output(*, role: str, metrics: dict) -> dict:
    out = {
        "engine": {"name": "bnk-analysis-engine", "version": "v1"},
        "analysis_id": "00000000-0000-0000-0000-000000000000",
        "created_at": "2026-02-06T00:00:00Z",
        "role": role,
        "track": {"duration_seconds": 1.0, "format": "wav", "sample_rate_hz": 44100, "channels": 2},
        "metrics": metrics,
        "warnings": [],
    }
    if role == "guest":
        out["events"] = {}
    return out


def test_locked_metric_contains_confidence_fails():
    out = _base_output(role="free", metrics={"grid": {"locked": True, "unlock_hint": "x", "confidence": 0.1}})
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_locked_metric_contains_candidates_fails():
    out = _base_output(role="free", metrics={"grid": {"locked": True, "unlock_hint": "x", "candidates": []}})
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_locked_metric_contains_evidence_fails():
    out = _base_output(role="free", metrics={"grid": {"locked": True, "unlock_hint": "x", "evidence": {"k": 1}}})
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_locked_metric_contains_value_fails():
    out = _base_output(role="free", metrics={"grid": {"locked": True, "unlock_hint": "x", "value": {"a": 1}}})
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_locked_metric_preview_empty_fails():
    out = _base_output(role="free", metrics={"grid": {"locked": True, "unlock_hint": "x", "preview": {}}})
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_guest_events_non_empty_fails():
    out = _base_output(role="guest", metrics={})
    out["events"] = {"clipping": {"sample_clipping_ranges": []}}
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_guest_bpm_value_exact_fails():
    out = _base_output(
        role="guest",
        metrics={"bpm": {"value": {"value_rounded": 70, "value_exact": 69.8}}},
    )
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(out)


def test_guest_smoke_valid_events_empty_and_bpm_no_value_exact_passes():
    out = _base_output(role="guest", metrics={"bpm": {"value": {"value_rounded": 70}}})
    validate_analysis_output_v1(out)

