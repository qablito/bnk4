#!/usr/bin/env bash
set -euo pipefail
python -c 'import sys; assert sys.version_info[:2] == (3, 11), sys.version'

PY_TARGETS=(engine conftest.py)
[ -d CHECKS ] && PY_TARGETS+=(CHECKS)

python -m ruff format --check "${PY_TARGETS[@]}"
python -m ruff check "${PY_TARGETS[@]}"
python -m pytest -q

