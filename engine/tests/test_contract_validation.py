import pytest

from engine.contracts.analysis_output import (
    ContractViolation,
    ValidateOptions,
    validate_analysis_output_v1,
)


def _base(role: str):
    return {
        "engine": {"name": "bnk-analysis-engine", "version": "v1"},
        "analysis_id": "11111111-1111-1111-1111-111111111111",
        "created_at": "2026-02-06T00:00:00Z",
        "role": role,
        "track": {"duration_seconds": 1.0, "format": "wav", "sample_rate_hz": 44100, "channels": 2},
        "metrics": {},
        "warnings": [],
    }


def test_guest_requires_events_empty_object():
    obj = _base("guest")
    obj["events"] = {}
    validate_analysis_output_v1(obj, opts=ValidateOptions(guest_events_policy="empty_object"))


def test_guest_locked_block_forbids_confidence_and_empty_preview():
    obj = _base("guest")
    obj["events"] = {}
    obj["metrics"]["grid"] = {"locked": True, "unlock_hint": "Upgrade", "preview": {}}
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(obj)

    obj["metrics"]["grid"] = {"locked": True, "unlock_hint": "Upgrade"}
    validate_analysis_output_v1(obj)


def test_guest_candidates_only_ranked_value():
    obj = _base("guest")
    obj["events"] = {}
    obj["metrics"]["bpm"] = {
        "value": {"value_rounded": 120},
        "candidates": [{"value": {"value_rounded": 120}, "rank": 1}],
    }
    validate_analysis_output_v1(obj)

    obj["metrics"]["bpm"]["candidates"][0]["score"] = 0.9
    with pytest.raises(ContractViolation):
        validate_analysis_output_v1(obj)
