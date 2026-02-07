#!/usr/bin/env bash
set -euo pipefail

if command -v pyenv >/dev/null 2>&1 && [[ -f .python-version ]]; then
  pyenv install -s "$(cat .python-version)"
  pyenv local "$(cat .python-version)"
fi

rm -rf .venv
if command -v python3.11 >/dev/null 2>&1; then
  python3.11 -m venv .venv
else
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]" --no-build-isolation
python -m pytest -q
