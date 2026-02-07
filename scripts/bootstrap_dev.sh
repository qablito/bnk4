#!/usr/bin/env bash
set -euo pipefail

# Ensure pyenv uses repo pin
if command -v pyenv >/dev/null 2>&1; then
  pyenv install -s "$(cat .python-version)"
  pyenv local "$(cat .python-version)"
else
  echo "pyenv not found. Install with: brew install pyenv"
  exit 1
fi

rm -rf .venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]" --no-build-isolation
python -m pytest -q
