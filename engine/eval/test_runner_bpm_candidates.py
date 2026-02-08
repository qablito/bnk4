from __future__ import annotations

from engine.eval.eval_types import Fixture, PredictionResult
from engine.eval.runner import _extract_bpm


def test_extract_bpm_preserves_candidates_even_when_value_is_omitted() -> None:
    """
    DO NOT LIE: even if bpm.value is omitted due to low confidence, the runner
    should still preserve candidates for diagnostics + eval reporting.
    """
    fx = Fixture(
        path="x.wav",
        bpm_gt_raw=None,
        bpm_gt_reportable=None,
        key_gt=None,
        mode_gt=None,
        flags=set(),
        notes="",
    )
    r = PredictionResult(fixture=fx, success=True, error=None, output=None)

    metrics = {
        "bpm": {
            "confidence": "low",
            "value": None,
            "candidates": [
                {"rank": 1, "value": {"value_rounded": 120}, "score": 0.9, "relation": "normal"},
                {"rank": 2, "value": {"value_rounded": 60}, "score": 0.3, "relation": "half"},
            ],
        }
    }

    _extract_bpm(r, metrics)
    assert r.bpm_omitted is True
    assert r.bpm_candidates is not None
    assert [c["value"]["value_rounded"] for c in r.bpm_candidates] == [120, 60]


def test_extract_bpm_preserves_reason_codes_for_omission_diagnostics() -> None:
    fx = Fixture(
        path="x.wav",
        bpm_gt_raw=None,
        bpm_gt_reportable=None,
        key_gt=None,
        mode_gt=None,
        flags=set(),
        notes="",
    )
    r = PredictionResult(fixture=fx, success=True, error=None, output=None)

    metrics = {
        "bpm": {
            "confidence": "low",
            "value": None,
            "bpm_reason_codes": ["omitted_ambiguous_runnerup", "omitted_low_confidence"],
        }
    }

    _extract_bpm(r, metrics)
    assert r.bpm_omitted is True
    assert r.bpm_reason_codes == ["omitted_ambiguous_runnerup", "omitted_low_confidence"]
