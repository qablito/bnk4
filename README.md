# bnk-analysis-engine (Engine v1)

Contract-first audio analysis engine for BeetsNKeys (bnk4).

References:
- Engine spec: `ANALYSIS_ENGINE_V1.md`
- Canonical output contract: `CONTRACTS/analysis_output.md`
- Security invariants + normalized error model: `SECURITY_SPEC.md`

## Development

Editable install:
```sh
python -m pip install -e ".[dev]" --no-build-isolation
```

Run tests:
```sh
python -m pytest -q
```

Build artifacts:
```sh
python -m build
python -m twine check dist/*
```

Note: Engine v1 intentionally avoids heavy audio dependencies (no numpy/librosa/etc).

