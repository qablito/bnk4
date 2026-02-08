"""Tests for metric computation."""

from __future__ import annotations

import pytest

from engine.eval.eval_types import Fixture, PredictionResult
from engine.eval.metrics import compute_metrics, format_text_report, metrics_to_json


def _make_fixture(
    path: str = "test.wav",
    bpm_gt_raw: float | None = None,
    bpm_gt_reportable: float | None = None,
    key_gt: str | None = None,
    mode_gt: str | None = None,
    flags: set[str] | None = None,
) -> Fixture:
    """Helper to create a fixture."""
    return Fixture(
        path=path,
        bpm_gt_raw=bpm_gt_raw,
        bpm_gt_reportable=bpm_gt_reportable,
        key_gt=key_gt,
        mode_gt=mode_gt,
        flags=flags or set(),
        notes="",
    )


def _make_result(
    fixture: Fixture,
    success: bool = True,
    bpm_value_rounded: int | None = None,
    bpm_omitted: bool = True,
    bpm_raw_value_rounded: int | None = None,
    bpm_raw_omitted: bool = True,
    bpm_reason_codes: list[str] | None = None,
    skipped: bool = False,
) -> PredictionResult:
    """Helper to create a prediction result."""
    return PredictionResult(
        fixture=fixture,
        success=success,
        error=None if success else "Test error",
        output={"metrics": {}} if success else None,
        skipped=skipped,
        bpm_value_rounded=bpm_value_rounded,
        bpm_omitted=bpm_omitted,
        bpm_raw_value_rounded=bpm_raw_value_rounded,
        bpm_raw_omitted=bpm_raw_omitted,
        bpm_reason_codes=bpm_reason_codes,
    )


def test_compute_metrics_empty_results() -> None:
    """Test computing metrics with no results."""
    metrics = compute_metrics([])
    assert metrics.total_fixtures == 0
    assert metrics.successful_runs == 0
    assert metrics.failed_runs == 0
    assert metrics.skipped_runs == 0
    assert metrics.bpm_reportable_n_total_strict == 0
    assert metrics.bpm_reportable_mae is None
    assert metrics.bpm_reportable_omit_rate is None
    assert metrics.bpm_raw_n_total_strict == 0
    assert metrics.bpm_raw_mae is None
    assert metrics.bpm_raw_omit_rate is None


def test_compute_metrics_failed_runs() -> None:
    """Test that failed runs are counted correctly."""
    f1 = _make_fixture("test1.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"})
    f2 = _make_fixture("test2.wav", bpm_gt_reportable=140.0, flags={"bpm_strict"})

    r1 = _make_result(f1, success=True, bpm_value_rounded=120, bpm_omitted=False)
    r2 = _make_result(f2, success=False)

    metrics = compute_metrics([r1, r2])
    assert metrics.total_fixtures == 2
    assert metrics.successful_runs == 1
    assert metrics.failed_runs == 1
    assert metrics.skipped_runs == 0
    # Only successful runs count for strict evaluation
    assert metrics.bpm_reportable_n_total_strict == 1


def test_compute_metrics_skipped_runs() -> None:
    """Test that skipped runs are counted correctly."""
    f1 = _make_fixture("test1.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"})
    f2 = _make_fixture("test2.wav", bpm_gt_reportable=140.0, flags={"bpm_strict"})

    r1 = _make_result(f1, success=True, bpm_value_rounded=120, bpm_omitted=False)
    r2 = _make_result(f2, success=False, skipped=True)

    metrics = compute_metrics([r1, r2])
    assert metrics.total_fixtures == 2
    assert metrics.successful_runs == 1
    assert metrics.failed_runs == 0
    assert metrics.skipped_runs == 1


def test_compute_metrics_bpm_mae() -> None:
    """Test BPM MAE computation (reportable)."""
    fixtures = [
        _make_fixture("test1.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"}),
        _make_fixture("test2.wav", bpm_gt_reportable=140.0, flags={"bpm_strict"}),
        _make_fixture("test3.wav", bpm_gt_reportable=100.0, flags={"bpm_strict"}),
    ]

    results = [
        _make_result(fixtures[0], bpm_value_rounded=122, bpm_omitted=False),  # error = 2
        _make_result(fixtures[1], bpm_value_rounded=135, bpm_omitted=False),  # error = 5
        _make_result(fixtures[2], bpm_value_rounded=101, bpm_omitted=False),  # error = 1
    ]

    metrics = compute_metrics(results)
    assert metrics.bpm_reportable_n_total_strict == 3
    assert metrics.bpm_reportable_n_predicted == 3
    assert metrics.bpm_reportable_n_omitted == 0
    # MAE = (2 + 5 + 1) / 3 = 2.667
    assert metrics.bpm_reportable_mae == pytest.approx(2.667, abs=0.01)
    assert metrics.bpm_reportable_omit_rate == 0.0


def test_compute_metrics_bpm_omissions() -> None:
    """Test BPM omission counting and omit_rate."""
    fixtures = [
        _make_fixture("test1.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"}),
        _make_fixture("test2.wav", bpm_gt_reportable=140.0, flags={"bpm_strict"}),
        _make_fixture("test3.wav", bpm_gt_reportable=100.0, flags={"bpm_strict"}),
    ]

    results = [
        _make_result(fixtures[0], bpm_value_rounded=122, bpm_omitted=False),  # predicted
        _make_result(fixtures[1], bpm_omitted=True),  # omitted
        _make_result(fixtures[2], bpm_value_rounded=101, bpm_omitted=False),  # predicted
    ]

    metrics = compute_metrics(results)
    assert metrics.bpm_reportable_n_total_strict == 3
    assert metrics.bpm_reportable_n_predicted == 2
    assert metrics.bpm_reportable_n_omitted == 1
    # MAE only computed on predictions
    assert metrics.bpm_reportable_mae == pytest.approx(1.5, abs=0.01)
    # Omit rate = 1/3
    assert metrics.bpm_reportable_omit_rate == pytest.approx(0.333, abs=0.01)


def test_compute_metrics_top_bpm_errors() -> None:
    """Test top N BPM errors extraction."""
    fixtures = [
        _make_fixture(f"test{i}.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"})
        for i in range(5)
    ]

    results = [
        _make_result(fixtures[0], bpm_value_rounded=125, bpm_omitted=False),  # error = 5
        _make_result(fixtures[1], bpm_value_rounded=130, bpm_omitted=False),  # error = 10
        _make_result(fixtures[2], bpm_value_rounded=121, bpm_omitted=False),  # error = 1
        _make_result(fixtures[3], bpm_value_rounded=118, bpm_omitted=False),  # error = 2
        _make_result(fixtures[4], bpm_value_rounded=113, bpm_omitted=False),  # error = 7
    ]

    metrics = compute_metrics(results, top_n_errors=3)
    assert len(metrics.top_bpm_errors_reportable) == 3

    # Check sorted by error descending
    assert metrics.top_bpm_errors_reportable[0].abs_error == 10.0
    assert metrics.top_bpm_errors_reportable[1].abs_error == 7.0
    assert metrics.top_bpm_errors_reportable[2].abs_error == 5.0


def test_compute_metrics_non_strict_ignored() -> None:
    """Test that non-strict fixtures are ignored in metrics."""
    fixtures = [
        _make_fixture(
            "strict.wav",
            bpm_gt_reportable=120.0,
            flags={"bpm_strict"},
        ),
        _make_fixture(
            "non_strict.wav",
            bpm_gt_reportable=140.0,
            flags=set(),  # Not bpm_strict
        ),
    ]

    results = [
        _make_result(fixtures[0], bpm_value_rounded=122, bpm_omitted=False),
        _make_result(fixtures[1], bpm_value_rounded=145, bpm_omitted=False),
    ]

    metrics = compute_metrics(results)
    # Only strict fixture counted
    assert metrics.bpm_reportable_n_total_strict == 1
    assert metrics.bpm_reportable_mae == 2.0


def test_compute_metrics_all_omitted() -> None:
    """Test metrics when all predictions are omitted."""
    fixtures = [
        _make_fixture("test1.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"}),
        _make_fixture("test2.wav", bpm_gt_reportable=140.0, flags={"bpm_strict"}),
    ]

    results = [
        _make_result(fixtures[0], bpm_omitted=True),
        _make_result(fixtures[1], bpm_omitted=True),
    ]

    metrics = compute_metrics(results)
    assert metrics.bpm_reportable_n_total_strict == 2
    assert metrics.bpm_reportable_n_predicted == 0
    assert metrics.bpm_reportable_n_omitted == 2
    assert metrics.bpm_reportable_mae is None  # Can't compute MAE with no predictions
    assert metrics.bpm_reportable_omit_rate == 1.0


def test_metrics_to_json_serializable() -> None:
    """Test that metrics_to_json produces JSON-serializable output."""
    import json

    fixtures = [
        _make_fixture("test.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"}),
    ]
    results = [
        _make_result(fixtures[0], bpm_value_rounded=122, bpm_omitted=False),
    ]

    metrics = compute_metrics(results)
    json_dict = metrics_to_json(metrics)

    # Should be JSON-serializable
    json_str = json.dumps(json_dict)
    assert isinstance(json_str, str)

    # Check structure
    parsed = json.loads(json_str)
    assert "overall" in parsed
    assert "bpm" in parsed
    assert "key_mode" in parsed
    assert "top_bpm_errors" in parsed

    # Check stable keys
    assert parsed["bpm_reportable"]["n_total_strict"] == 1
    assert parsed["bpm_reportable"]["n_predicted"] == 1
    assert parsed["bpm_reportable"]["mae"] == 2.0
    assert parsed["bpm_reportable"]["omit_rate"] == 0.0


def test_format_text_report() -> None:
    """Test that text report is properly formatted."""
    fixtures = [
        _make_fixture("test.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"}),
    ]
    results = [
        _make_result(fixtures[0], bpm_value_rounded=130, bpm_omitted=False),
    ]

    metrics = compute_metrics(results)
    report = format_text_report(metrics)

    assert "BeetsNKeys Analysis Engine v1" in report
    assert "Total fixtures: 1" in report
    assert "MAE: 10.00 BPM" in report
    assert "Omit rate: 0.0%" in report
    assert "test.wav" in report
    assert "GT: 120.0 BPM" in report
    assert "Predicted: 130 BPM" in report


def test_compute_metrics_with_candidates() -> None:
    """Test that candidates are preserved in error details."""
    f = _make_fixture("test.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"})

    r = PredictionResult(
        fixture=f,
        success=True,
        error=None,
        output={"metrics": {}},
        bpm_value_rounded=60,  # Half-time error
        bpm_omitted=False,
        bpm_candidates=[
            {"value": {"value_rounded": 60}, "rank": 1},
            {"value": {"value_rounded": 120}, "rank": 2},
        ],
    )

    metrics = compute_metrics([r])
    assert len(metrics.top_bpm_errors_reportable) == 1

    err = metrics.top_bpm_errors_reportable[0]
    assert err.abs_error == 60.0
    assert err.candidates == [60, 120]


def test_compute_metrics_raw_vs_reportable_and_confusion_stats() -> None:
    """
    If raw/reportable differ by 2x, metrics should compute both MAEs and record confusions.
    """
    f = _make_fixture(
        "trap.wav",
        bpm_gt_raw=85.0,
        bpm_gt_reportable=170.0,
        flags={"bpm_strict", "double_time_preferred"},
    )
    # Reportable vs raw predictions are tracked separately.
    r = _make_result(
        f,
        bpm_value_rounded=170,
        bpm_omitted=False,
        bpm_raw_value_rounded=85,
        bpm_raw_omitted=False,
    )

    metrics = compute_metrics([r], top_n_errors=10)

    # Raw MAE is 0, reportable MAE is 0 (separate predictions).
    assert metrics.bpm_raw_mae == pytest.approx(0.0, abs=0.01)
    assert metrics.bpm_reportable_mae == pytest.approx(0.0, abs=0.01)

    assert metrics.bpm_half_double_confusion_count == 1
    assert metrics.bpm_half_double_confusions[0].path == "trap.wav"


def test_bpm_family_match_rate_reportable_counts_half_double_as_match() -> None:
    f1 = _make_fixture("a.wav", bpm_gt_reportable=170.0, flags={"bpm_strict"})
    f2 = _make_fixture("b.wav", bpm_gt_reportable=120.0, flags={"bpm_strict"})

    r1 = _make_result(f1, bpm_value_rounded=85, bpm_omitted=False)  # half-time
    r2 = _make_result(f2, bpm_value_rounded=100, bpm_omitted=False)  # mismatch

    metrics = compute_metrics([r1, r2], bpm_tolerance=1.0)
    assert metrics.bpm_family_match_rate_reportable == pytest.approx(0.5, abs=0.001)


def test_compute_metrics_reportable_omit_reason_breakdown_and_policy_flip_rate() -> None:
    f1 = _make_fixture("a.wav", bpm_gt_raw=70.0, bpm_gt_reportable=140.0, flags={"bpm_strict"})
    f2 = _make_fixture("b.wav", bpm_gt_raw=85.0, bpm_gt_reportable=170.0, flags={"bpm_strict"})
    f3 = _make_fixture("c.wav", bpm_gt_raw=90.0, bpm_gt_reportable=90.0, flags={"bpm_strict"})

    r1 = _make_result(
        f1,
        bpm_value_rounded=None,
        bpm_omitted=True,
        bpm_raw_value_rounded=70,
        bpm_raw_omitted=False,
        bpm_reason_codes=["omitted_ambiguous_runnerup", "omitted_low_confidence"],
    )
    r2 = _make_result(
        f2,
        bpm_value_rounded=170,
        bpm_omitted=False,
        bpm_raw_value_rounded=85,
        bpm_raw_omitted=False,
        bpm_reason_codes=["prefer_double_time_from_raw", "has_direct_double_evidence"],
    )
    r3 = _make_result(
        f3,
        bpm_value_rounded=90,
        bpm_omitted=False,
        bpm_raw_value_rounded=90,
        bpm_raw_omitted=False,
        bpm_reason_codes=["prefer_raw"],
    )

    metrics = compute_metrics([r1, r2, r3], bpm_tolerance=1.0)
    assert metrics.bpm_reportable_omit_reason_counts == {
        "omitted_ambiguous_runnerup": 1,
        "omitted_low_confidence": 1,
    }
    # Only emitted reportable rows with raw available count. r2 flips family, r3 does not.
    assert metrics.bpm_policy_flip_rate == pytest.approx(0.5, abs=0.001)


def test_compute_metrics_half_double_confusion_matrix() -> None:
    f1 = _make_fixture("a.wav", bpm_gt_raw=70.0, bpm_gt_reportable=140.0, flags={"bpm_strict"})
    f2 = _make_fixture("b.wav", bpm_gt_raw=75.0, bpm_gt_reportable=150.0, flags={"bpm_strict"})
    f3 = _make_fixture("c.wav", bpm_gt_raw=85.0, bpm_gt_reportable=170.0, flags={"bpm_strict"})

    r1 = _make_result(f1, bpm_value_rounded=70, bpm_omitted=False)  # matches raw
    r2 = _make_result(f2, bpm_value_rounded=150, bpm_omitted=False)  # matches reportable
    r3 = _make_result(f3, bpm_value_rounded=111, bpm_omitted=False)  # matches neither

    metrics = compute_metrics([r1, r2, r3], bpm_tolerance=1.0)
    assert metrics.bpm_half_double_confusion_matrix == {
        "pred_matches_raw": 1,
        "pred_matches_reportable": 1,
        "pred_matches_both": 0,
        "pred_matches_neither": 1,
        "gt_missing": 0,
    }

    json_blob = metrics_to_json(metrics)
    assert json_blob["bpm_half_double_confusion_matrix"]["pred_matches_raw"] == 1


def test_confusion_matrix_predicted_double_of_reportable_counts_as_neither() -> None:
    f = _make_fixture(
        "reggaeton.wav", bpm_gt_raw=88.0, bpm_gt_reportable=88.0, flags={"bpm_strict"}
    )
    r = _make_result(f, bpm_value_rounded=176, bpm_omitted=False)

    metrics = compute_metrics([r], bpm_tolerance=1.0)
    assert metrics.bpm_half_double_confusion_matrix == {
        "pred_matches_raw": 0,
        "pred_matches_reportable": 0,
        "pred_matches_both": 0,
        "pred_matches_neither": 1,
        "gt_missing": 0,
    }


def test_confusion_matrix_excludes_fixtures_with_missing_gt() -> None:
    f = _make_fixture(
        "reggaeton__80__Aminor__preguntandome.wav",
        bpm_gt_raw=None,
        bpm_gt_reportable=None,
        flags={"bpm_strict"},
    )
    r = _make_result(f, bpm_value_rounded=80, bpm_omitted=False, bpm_reason_codes=["prefer_raw"])

    metrics = compute_metrics([r], bpm_tolerance=1.0)
    assert metrics.bpm_half_double_confusion_matrix == {
        "pred_matches_raw": 0,
        "pred_matches_reportable": 0,
        "pred_matches_both": 0,
        "pred_matches_neither": 0,
        "gt_missing": 1,
    }


def test_confusion_matrix_counts_gt_missing_outside_bpm_strict_pool() -> None:
    with_gt = _make_fixture(
        "trap.wav",
        bpm_gt_raw=70.0,
        bpm_gt_reportable=140.0,
        flags={"bpm_strict"},
    )
    missing_gt = _make_fixture(
        "preguntandome.wav",
        bpm_gt_raw=None,
        bpm_gt_reportable=None,
        flags={"key_strict", "ambiguous"},
    )

    r1 = _make_result(with_gt, bpm_value_rounded=70, bpm_omitted=False)
    r2 = _make_result(missing_gt, bpm_value_rounded=80, bpm_omitted=False)

    metrics = compute_metrics([r1, r2], bpm_tolerance=1.0)
    assert metrics.bpm_half_double_confusion_matrix == {
        "pred_matches_raw": 1,
        "pred_matches_reportable": 0,
        "pred_matches_both": 0,
        "pred_matches_neither": 0,
        "gt_missing": 1,
    }
