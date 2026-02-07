#!/usr/bin/env bash
set -euo pipefail

ruff format --check .
ruff check .
python -m pytest -q

