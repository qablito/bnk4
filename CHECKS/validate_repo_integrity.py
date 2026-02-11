#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = [
    "apps/analyzer-web/package.json",
    "apps/analyzer-web/src/app/page.tsx",
    "apps/analyzer-api/api.py",
    "apps/analyzer-api/service.py",
]


def find_missing_paths(root: Path) -> list[str]:
    missing: list[str] = []
    for rel_path in REQUIRED_PATHS:
        if not (root / rel_path).is_file():
            missing.append(rel_path)
    return missing


def main() -> int:
    missing = find_missing_paths(REPO_ROOT)
    if missing:
        print("Repository integrity check failed. Missing required repository paths:")
        for rel_path in missing:
            print(f"- {rel_path}")
        return 1

    print("Repository integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
