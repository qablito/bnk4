from __future__ import annotations

from pathlib import Path

from CHECKS import validate_repo_integrity as integrity


def _touch_required_files(root: Path) -> None:
    for rel_path in integrity.REQUIRED_PATHS:
        file_path = root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("ok", encoding="utf-8")


def test_find_missing_paths_reports_required_files(tmp_path: Path) -> None:
    missing = integrity.find_missing_paths(tmp_path)
    assert missing == integrity.REQUIRED_PATHS


def test_find_missing_paths_returns_empty_when_all_files_exist(tmp_path: Path) -> None:
    _touch_required_files(tmp_path)
    assert integrity.find_missing_paths(tmp_path) == []


def test_main_prints_missing_paths_and_returns_error(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(integrity, "REPO_ROOT", tmp_path)
    exit_code = integrity.main()

    captured = capsys.readouterr().out
    assert exit_code == 1
    assert "Repository integrity check failed." in captured
    assert "- apps/analyzer-web/package.json" in captured
    assert "- apps/analyzer-api/api.py" in captured
