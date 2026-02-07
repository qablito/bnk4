# bnk-analysis-engine (Engine v1)

Contract-first audio analysis engine for BeetsNKeys (bnk4).

References:
- Engine spec: `ANALYSIS_ENGINE_V1.md`
- Canonical output contract: `CONTRACTS/analysis_output.md`
- Security invariants + normalized error model: `SECURITY_SPEC.md`

## Tooling

Bootstrap a local venv and run tests:
```sh
./scripts/bootstrap_dev.sh
source .venv/bin/activate
```

Format:
```sh
./scripts/fmt.sh
```

Lint + tests:
```sh
./scripts/lint.sh
```

Optional pre-commit:
```sh
python -m pip install pre-commit
pre-commit install
```

Build artifacts:
```sh
python -m build
python -m twine check dist/*
```

Note: Engine v1 intentionally avoids heavy audio dependencies (no numpy/librosa/etc).
