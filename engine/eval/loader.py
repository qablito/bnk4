"""Load fixtures from CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from engine.eval.eval_types import Fixture

# Required columns (must be present in header)
REQUIRED_COLUMNS = {"path", "bpm_gt", "key_gt", "mode_gt", "flags", "notes"}

# Known optional columns (parsed specially)
KNOWN_COLUMNS = REQUIRED_COLUMNS | {
    "genre",
    "bpm_reportable",
    "bpm_raw",
    "timefeel",
    "bars",
    "sections",
    "drift",
}


def load_fixtures(csv_path: Path) -> list[Fixture]:
    """
    Load fixtures from CSV file.

    CSV format:
        path,bpm_gt,key_gt,mode_gt,flags,notes[,extra columns...]

    Comments (lines starting with #) and empty rows are skipped.
    Unknown columns are preserved in fixture.extra dict.

    Returns:
        List of Fixture objects.

    Raises:
        FileNotFoundError: If CSV file doesn't exist.
        ValueError: If CSV format is invalid.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Fixtures CSV not found: {csv_path}")

    fixtures = []
    with csv_path.open("r", encoding="utf-8") as f:
        # Read first line to check header
        first_line = f.readline().strip()
        if not first_line:
            raise ValueError(f"Empty CSV or missing header: {csv_path}")

        # Check if first line is a comment
        if first_line.startswith("#"):
            raise ValueError(f"CSV header cannot be a comment: {csv_path}")

        # Parse header
        f.seek(0)
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"Could not parse CSV header: {csv_path}")

        # Validate required columns
        header_set = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - header_set
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            # Skip empty rows and comments
            path_val = row.get("path", "").strip()
            if not path_val or path_val.startswith("#"):
                continue

            try:
                fixture = _parse_fixture_row(row, reader.fieldnames)
                fixtures.append(fixture)
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Invalid fixture at row {row_num}: {exc}") from exc

    return fixtures


def _parse_fixture_row(row: dict[str, str], fieldnames: list[str]) -> Fixture:
    """Parse a single CSV row into a Fixture."""
    path = row["path"].strip()
    if not path:
        raise ValueError("path cannot be empty")

    # Parse ground truth values (empty = None)
    bpm_gt = _parse_optional_float(row.get("bpm_gt", ""))
    key_gt = _parse_optional_string(row.get("key_gt", ""))
    mode_gt = _parse_optional_string(row.get("mode_gt", ""))

    # Parse flags (comma-separated)
    flags_str = row.get("flags", "").strip()
    flags = set()
    if flags_str:
        for flag in flags_str.split(","):
            flag = flag.strip()
            if flag:
                flags.add(flag)

    notes = row.get("notes", "").strip()

    # Collect extra columns
    extra = {}
    for col in fieldnames:
        if col not in REQUIRED_COLUMNS:
            val = row.get(col, "").strip()
            if val:
                extra[col] = val

    return Fixture(
        path=path,
        bpm_gt=bpm_gt,
        key_gt=key_gt,
        mode_gt=mode_gt,
        flags=flags,
        notes=notes,
        extra=extra,
    )


def _parse_optional_float(s: str) -> float | None:
    """Parse optional float (empty string -> None)."""
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError as exc:
        raise ValueError(f"Invalid float: {s!r}") from exc


def _parse_optional_string(s: str) -> str | None:
    """Parse optional string (empty string -> None)."""
    s = s.strip()
    return s if s else None
