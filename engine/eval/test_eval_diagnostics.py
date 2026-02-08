from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.core.errors import EngineError
from engine.eval.eval_types import Fixture
from engine.eval.runner import run_fixture


def test_run_fixture_missing_file_has_reason_code(tmp_path: Path) -> None:
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
    assert result.skip_reason_code == "file_not_found"


def test_run_eval_json_includes_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "fixtures.csv"
    out_path = tmp_path / "out.json"
    csv_path.write_text(
        "path,bpm_gt,key_gt,mode_gt,flags,notes\n"
        f"{tmp_path / 'nope.wav'},120,C,major,bpm_strict,\n",
        encoding="utf-8",
    )

    from engine.eval import run_eval

    monkeypatch.setattr(
        run_eval.sys,
        "argv",
        ["run_eval.py", "--fixtures", str(csv_path), "--output", str(out_path)],
    )

    rc = run_eval.main()
    assert rc == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert "skipped" in report
    assert report["skipped"][0]["reason_code"] == "file_not_found"

    # Deterministic per-fixture debug export (even when skipped).
    assert "fixtures" in report
    assert len(report["fixtures"]) == 1
    fx = report["fixtures"][0]
    assert fx["path"].endswith("nope.wav")
    assert fx["bpm_gt_raw"] is None
    assert fx["bpm_gt_reportable"] == 120.0
    assert fx["predicted_bpm_value_rounded"] is None
    assert fx["predicted_bpm_confidence"] is None
    assert fx["top_candidates_rounded"] == []

    hs = fx["bpm_hint_windows_summary"]
    assert hs["count"] == 0
    assert hs["median"] is None
    assert hs["iqr"] is None


def test_failure_captures_stage_and_exc_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "fake.wav"
    p.write_bytes(b"not a real wav")

    import engine.eval.runner as runner

    def boom(*_args: object, **_kwargs: object) -> dict:
        raise EngineError(
            code="UNSUPPORTED_INPUT", message="Unsupported", context={"stage": "decode"}
        )

    monkeypatch.setattr(runner, "run_analysis_v1", boom)

    f = Fixture(
        path=str(p),
        bpm_gt_raw=None,
        bpm_gt_reportable=120.0,
        key_gt=None,
        mode_gt=None,
        flags=set(),
        notes="",
    )
    result = run_fixture(f)
    assert result.success is False
    assert result.failure is not None
    assert result.failure["stage"] == "decode"
    assert result.failure["exc_type"] == "EngineError"
