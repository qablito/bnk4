"""Integration tests for evaluation harness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.eval.eval_types import Fixture, PredictionResult
from engine.eval.loader import load_fixtures
from engine.eval.metrics import compute_metrics, format_text_report, metrics_to_json
from engine.eval.runner import run_all_fixtures, run_fixture


def test_end_to_end_empty_fixtures(tmp_path: Path) -> None:
    """Test end-to-end evaluation with empty fixtures (only comments)."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
# Only comments here
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 0

    results = run_all_fixtures(fixtures)
    assert len(results) == 0

    metrics = compute_metrics(results)
    assert metrics.total_fixtures == 0
    assert metrics.bpm_reportable_mae is None
    assert metrics.bpm_raw_mae is None


def test_run_fixture_missing_file(tmp_path: Path) -> None:
    """Test that missing files are handled gracefully when not fail_on_missing."""
    f = Fixture(
        path=str(tmp_path / "nonexistent.wav"),
        bpm_gt_raw=None,
        bpm_gt_reportable=120.0,
        key_gt="C",
        mode_gt="major",
        flags={"bpm_strict"},
        notes="",
    )

    result = run_fixture(f, fail_on_missing=False)
    assert result.skipped is True
    assert result.success is False
    assert "not found" in (result.skip_reason or "").lower()


def test_run_fixture_missing_file_fail_mode(tmp_path: Path) -> None:
    """Test that missing files raise error when fail_on_missing=True."""
    f = Fixture(
        path=str(tmp_path / "nonexistent.wav"),
        bpm_gt_raw=None,
        bpm_gt_reportable=120.0,
        key_gt="C",
        mode_gt="major",
        flags={"bpm_strict"},
        notes="",
    )

    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        run_fixture(f, fail_on_missing=True)


def test_run_all_fixtures_with_limit(tmp_path: Path) -> None:
    """Test that limit parameter works."""
    fixtures = [
        Fixture(
            path=str(tmp_path / f"test{i}.wav"),
            bpm_gt_raw=None,
            bpm_gt_reportable=120.0,
            key_gt=None,
            mode_gt=None,
            flags=set(),
            notes="",
        )
        for i in range(10)
    ]

    results = run_all_fixtures(fixtures, limit=3, fail_on_missing=False)
    assert len(results) == 3


def test_json_report_stable_keys() -> None:
    """Test that JSON report has stable keys for diffing."""
    fixtures = [
        Fixture(
            path="test.wav",
            bpm_gt_raw=None,
            bpm_gt_reportable=120.0,
            key_gt="C",
            mode_gt="major",
            flags={"bpm_strict"},
            notes="",
        )
    ]

    results = [
        PredictionResult(
            fixture=fixtures[0],
            success=True,
            error=None,
            output={"metrics": {}},
            bpm_value_rounded=122,
            bpm_omitted=False,
        )
    ]

    metrics = compute_metrics(results)
    report = metrics_to_json(metrics)

    # Verify all expected keys are present
    assert set(report.keys()) == {
        "overall",
        "bpm",
        "bpm_reportable",
        "bpm_raw",
        "bpm_half_double_confusions",
        "bpm_half_double_confusion_count",
        "bpm_half_double_confusion_matrix",
        "key_mode",
        "top_bpm_errors",
        "top_bpm_errors_raw",
    }
    assert set(report["overall"].keys()) == {
        "total_fixtures",
        "successful_runs",
        "failed_runs",
        "skipped_runs",
    }
    assert set(report["bpm"].keys()) == {
        "n_total_strict",
        "n_predicted",
        "n_omitted",
        "mae",
        "omit_rate",
        "family_match_rate",
        "omit_reason_counts",
        "policy_flip_rate",
    }

    # Ensure JSON is deterministic
    json1 = json.dumps(report, sort_keys=True)
    json2 = json.dumps(report, sort_keys=True)
    assert json1 == json2


def test_text_report_formatting() -> None:
    """Test that text report is properly formatted."""
    from engine.eval.eval_types import BpmError, EvalMetrics

    metrics = EvalMetrics(
        total_fixtures=10,
        successful_runs=9,
        failed_runs=1,
        skipped_runs=0,
        bpm_reportable_n_total_strict=5,
        bpm_reportable_n_predicted=4,
        bpm_reportable_n_omitted=1,
        bpm_reportable_mae=2.5,
        bpm_reportable_omit_rate=0.2,
        bpm_family_match_rate_reportable=0.75,
        bpm_reportable_omit_reason_counts={"omitted_low_confidence": 1},
        bpm_policy_flip_rate=0.5,
        bpm_raw_n_total_strict=5,
        bpm_raw_n_predicted=4,
        bpm_raw_n_omitted=1,
        bpm_raw_mae=2.5,
        bpm_raw_omit_rate=0.2,
        top_bpm_errors_reportable=[
            BpmError(
                path="worst.wav",
                bpm_gt=120.0,
                bpm_pred=130,
                candidates=[130, 65],
                abs_error=10.0,
                notes="Test note",
                kind="reportable",
            )
        ],
        top_bpm_errors_raw=[],
        bpm_half_double_confusion_matrix={
            "pred_matches_raw": 0,
            "pred_matches_reportable": 0,
            "pred_matches_both": 0,
            "pred_matches_neither": 0,
        },
    )

    report = format_text_report(metrics)
    assert "Total fixtures: 10" in report
    assert "MAE: 2.50 BPM" in report
    assert "Omit rate: 20.0%" in report
    assert "worst.wav" in report
    assert "GT: 120.0 BPM" in report
    assert "Error: 10.0 BPM" in report
    assert "Candidates: [130, 65]" in report


def test_missing_ground_truth_handling(tmp_path: Path) -> None:
    """Test that fixtures with missing ground truth are handled gracefully."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
test_no_gt.wav,,,,short_audio,No ground truth
test_with_bpm.wav,120,,,bpm_strict,Only BPM ground truth
test_with_key.wav,,C,major,key_strict,Only key ground truth
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 3

    # Verify ground truth parsing
    assert fixtures[0].bpm_gt_reportable is None
    assert fixtures[0].bpm_gt_raw is None
    assert fixtures[0].key_gt is None
    assert fixtures[1].bpm_gt_reportable == 120.0
    assert fixtures[1].bpm_gt_raw is None
    assert fixtures[1].key_gt is None
    assert fixtures[2].bpm_gt_reportable is None
    assert fixtures[2].bpm_gt_raw is None
    assert fixtures[2].key_gt == "C"


def test_ambiguous_flag_preserved(tmp_path: Path) -> None:
    """Test that ambiguous flag is preserved through loading."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
test.wav,120,C,major,"ambiguous,bpm_strict",Multiple tempo interpretations
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 1
    assert fixtures[0].is_ambiguous
    assert fixtures[0].is_bpm_strict


@pytest.mark.skipif(
    not Path("engine/eval/samples").exists(),
    reason="Real audio samples not present",
)
def test_run_on_real_samples() -> None:
    """Integration test with real audio files (skipped if not present)."""
    fixtures_path = Path("engine/eval/fixtures.csv")
    if not fixtures_path.exists():
        pytest.skip("fixtures.csv not found")

    fixtures = load_fixtures(fixtures_path)
    if not fixtures:
        pytest.skip("No fixtures in CSV")

    # Limit to first 2 for speed
    fixtures = fixtures[:2]

    # Check if files exist
    existing = [f for f in fixtures if Path(f.path).exists()]
    if not existing:
        pytest.skip("No fixture audio files found")

    results = run_all_fixtures(existing, role="pro", fail_on_missing=False)
    metrics = compute_metrics(results)

    # Basic sanity checks
    assert metrics.total_fixtures == len(existing)
    assert metrics.successful_runs + metrics.failed_runs + metrics.skipped_runs == len(existing)
