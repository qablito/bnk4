# Development

## Environment
```bash
./scripts/bootstrap_dev.sh
source .venv/bin/activate
```

## Formatting and Lint
```bash
python3 -m ruff format engine conftest.py engine/eval engine/tests
python3 -m ruff check engine conftest.py engine/eval engine/tests
```

## Tests
```bash
pytest -q -rs
```

## Evaluation Harness
```bash
PYTHONPATH=. python3 engine/eval/run_eval.py \
  --fixtures engine/eval/fixtures.csv \
  --output /tmp/eval.json \
  --top-n 10
```

## Notes
- Engine v1 avoids heavy audio dependencies.
- Missing optional audio fixture(s) may skip specific integration tests.
- `apps/` is reserved for local API/UI work; engine validation remains under `engine/tests` and `engine/eval`.
