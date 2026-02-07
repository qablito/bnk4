#!/usr/bin/env bash
set -euo pipefail

PY_TARGETS=(engine conftest.py)
[ -d CHECKS ] && PY_TARGETS+=(CHECKS)

python -m ruff format "${PY_TARGETS[@]}"
python -m ruff check --fix "${PY_TARGETS[@]}"
