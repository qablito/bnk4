#!/usr/bin/env bash
set -euo pipefail

# CI must validate contract to prevent drift
export BNK_ENGINE_ASSERT_CONTRACT=1

./scripts/lint.sh
python -m build
python -m twine check dist/*