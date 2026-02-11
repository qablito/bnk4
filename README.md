# BeetsNKeys (bnk4)

BeetsNKeys is a contract-first audio analysis project focused on deterministic, role-safe outputs. In this repository, the main shipped component is the Engine v1 analysis core.

## Repository
- `engine/`: analysis pipeline, packaging, tests, and eval harness.
- `apps/`: local product surfaces (API/UI) built on top of engine outputs.
- `docs/`: project status, architecture, contract, and developer docs.
- `scripts/`: development helpers.

## Quickstart
```bash
./scripts/bootstrap_dev.sh
source .venv/bin/activate
python3 -m ruff format engine conftest.py engine/eval engine/tests
python3 -m ruff check engine conftest.py engine/eval engine/tests
pytest -q -rs
PYTHONPATH=. python3 engine/eval/run_eval.py --fixtures engine/eval/fixtures.csv --top-n 10
```

## Docs
- Project status: `docs/PROJECT_STATUS.md`
- Development guide: `docs/DEVELOPMENT.md`
- Architecture: `docs/ARCHITECTURE.md`
- Engine v1 contract: `docs/ENGINE_V1_CONTRACT.md`
- Security invariants: `docs/SECURITY_SPEC.md`
