#!/usr/bin/env bash
set -euo pipefail
python -c 'import sys; assert sys.version_info[:2] == (3, 11), sys.version'


ruff format --check .
ruff check .
python -m pytest -q
