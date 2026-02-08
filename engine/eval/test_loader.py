"""Tests for fixture loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.eval.eval_types import Fixture
from engine.eval.loader import load_fixtures


def test_load_fixtures_missing_file(tmp_path: Path) -> None:
    """Test loading non-existent CSV raises FileNotFoundError."""
    csv_path = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError, match="Fixtures CSV not found"):
        load_fixtures(csv_path)


def test_load_fixtures_empty_csv(tmp_path: Path) -> None:
    """Test loading empty CSV raises ValueError."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")

    with pytest.raises(ValueError, match="Empty CSV or missing header"):
        load_fixtures(csv_path)


def test_load_fixtures_missing_columns(tmp_path: Path) -> None:
    """Test loading CSV with missing required columns raises ValueError."""
    csv_path = tmp_path / "missing_cols.csv"
    csv_path.write_text("path,bpm_gt\n")  # Missing key_gt, mode_gt, flags, notes

    with pytest.raises(ValueError, match="Missing required columns"):
        load_fixtures(csv_path)


def test_load_fixtures_valid_data(tmp_path: Path) -> None:
    """Test loading valid CSV with mixed data."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
test1.wav,120.0,C,major,bpm_strict,Test fixture 1
test2.mp3,140.5,D#,minor,"key_strict,bpm_strict",Ambiguous case
test3.wav,,,,short_audio,No ground truth
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 3

    # Check first fixture
    f1 = fixtures[0]
    assert f1.path == "test1.wav"
    assert f1.bpm_gt_reportable == 120.0
    assert f1.bpm_gt_raw is None
    assert f1.key_gt == "C"
    assert f1.mode_gt == "major"
    assert f1.is_bpm_strict
    assert not f1.is_key_strict
    assert f1.notes == "Test fixture 1"

    # Check second fixture
    f2 = fixtures[1]
    assert f2.path == "test2.mp3"
    assert f2.bpm_gt_reportable == 140.5
    assert f2.bpm_gt_raw is None
    assert f2.key_gt == "D#"
    assert f2.mode_gt == "minor"
    assert f2.is_key_strict
    assert f2.is_bpm_strict

    # Check third fixture (no ground truth)
    f3 = fixtures[2]
    assert f3.path == "test3.wav"
    assert f3.bpm_gt_reportable is None
    assert f3.bpm_gt_raw is None
    assert f3.key_gt is None
    assert f3.mode_gt is None
    assert f3.is_short_audio


def test_load_fixtures_skip_comments_and_empty_rows(tmp_path: Path) -> None:
    """Test that comments and empty rows are skipped."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
# This is a comment
test1.wav,120,C,major,bpm_strict,Valid

# Another comment
test2.wav,140,D,minor,key_strict,Also valid
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 2
    assert fixtures[0].path == "test1.wav"
    assert fixtures[1].path == "test2.wav"


def test_load_fixtures_invalid_bpm(tmp_path: Path) -> None:
    """Test that invalid BPM values raise ValueError."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
test.wav,not_a_number,C,major,,Invalid BPM
"""
    csv_path.write_text(content)

    with pytest.raises(ValueError, match="Invalid fixture at row 2"):
        load_fixtures(csv_path)


def test_load_fixtures_extra_columns_preserved(tmp_path: Path) -> None:
    """Test that extra columns are preserved in fixture.extra."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes,genre,bars,custom_field
test.wav,120,C,major,bpm_strict,Test,trap,64,some_value
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 1
    f = fixtures[0]
    assert f.extra.get("genre") == "trap"
    assert f.extra.get("bars") == "64"
    assert f.extra.get("custom_field") == "some_value"


def test_load_fixtures_double_time_preferred_flag(tmp_path: Path) -> None:
    """Test that double_time_preferred flag is recognized."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
test.wav,170,C,major,"bpm_strict,double_time_preferred",Double-time trap
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 1
    assert fixtures[0].is_double_time_preferred
    assert fixtures[0].is_bpm_strict


def test_load_fixtures_empty_gt_fields(tmp_path: Path) -> None:
    """Test that empty ground truth fields are parsed as None."""
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
test.wav,,,,"key_strict,ambiguous",No BPM ground truth
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 1
    f = fixtures[0]
    assert f.bpm_gt is None
    assert f.key_gt is None
    assert f.mode_gt is None
    assert f.is_key_strict
    assert f.is_ambiguous
    assert not f.is_bpm_strict


def test_fixture_flags_properties() -> None:
    """Test Fixture flag properties work correctly."""
    f1 = Fixture(
        path="test.wav",
        bpm_gt_raw=None,
        bpm_gt_reportable=120,
        key_gt="C",
        mode_gt="major",
        flags={"bpm_strict"},
        notes="",
    )
    assert f1.is_bpm_strict
    assert not f1.is_key_strict
    assert not f1.is_ambiguous
    assert not f1.is_short_audio
    assert not f1.is_double_time_preferred

    f2 = Fixture(
        path="test2.wav",
        bpm_gt_raw=None,
        bpm_gt_reportable=140,
        key_gt="D",
        mode_gt="minor",
        flags={"key_strict", "ambiguous", "double_time_preferred"},
        notes="",
    )
    assert not f2.is_bpm_strict
    assert f2.is_key_strict
    assert f2.is_ambiguous
    assert f2.is_double_time_preferred
    assert not f2.is_short_audio


def test_load_fixtures_real_format(tmp_path: Path) -> None:
    """Test loading CSV matching the real fixtures.csv format."""
    csv_path = tmp_path / "fixtures.csv"
    # Use shorter paths and notes to avoid line length issues
    content = """path,bpm_gt,key_gt,mode_gt,flags,notes
samples/trap.mp3,170,B,minor,"bpm_strict,key_strict,double_time_preferred",trap beat
samples/rnb.mp3,92,G,minor,"bpm_strict,key_strict",rnb track
samples/reggaeton.mp3,,A,minor,"key_strict,ambiguous",approx 80 bpm
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 3

    # Trap fixture
    f_trap = fixtures[0]
    assert f_trap.bpm_gt_reportable == 170
    assert f_trap.key_gt == "B"
    assert f_trap.mode_gt == "minor"
    assert f_trap.is_bpm_strict
    assert f_trap.is_key_strict
    assert f_trap.is_double_time_preferred

    # RnB fixture
    f_rnb = fixtures[1]
    assert f_rnb.bpm_gt_reportable == 92
    assert not f_rnb.is_double_time_preferred

    # Reggaeton fixture (no BPM GT)
    f_reg = fixtures[2]
    assert f_reg.bpm_gt_reportable is None
    assert f_reg.is_ambiguous
    assert not f_reg.is_bpm_strict


def test_load_fixtures_new_bpm_columns_override_legacy_bpm_gt(tmp_path: Path) -> None:
    """
    If bpm_gt_raw/bpm_gt_reportable columns are present, they take precedence over legacy bpm_gt.
    """
    csv_path = tmp_path / "fixtures.csv"
    content = """path,bpm_gt_raw,bpm_gt_reportable,bpm_gt,key_gt,mode_gt,flags,notes
test.wav,85,170,999,C,minor,"bpm_strict,double_time_preferred",explicit raw/reportable
"""
    csv_path.write_text(content)

    fixtures = load_fixtures(csv_path)
    assert len(fixtures) == 1
    f = fixtures[0]
    assert f.bpm_gt_raw == 85.0
    assert f.bpm_gt_reportable == 170.0
