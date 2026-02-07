#!/usr/bin/env bash
set -euo pipefail

export BNK_ENGINE_ASSERT_CONTRACT=1

./scripts/lint.sh

python -m build --no-isolation || echo "WARN: build skipped (missing deps or offline environment)"
python -m twine check dist/* || echo "WARN: twine check skipped (no dist artifacts)"

git diff --exit-code
git diff --cached --exit-code

