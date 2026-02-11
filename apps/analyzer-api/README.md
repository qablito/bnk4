# BeetsNKeys Analyzer API (v1)

Local FastAPI wrapper around `engine/` for Engine v1 analysis.

## Scope (v1)

- Input: `sample_id` only
- Audio root: `audiosToTest/` (repo root) by default
- Uploads: not supported in v1 (planned for v1.1)

## Install

```bash
python3 -m pip install -r apps/analyzer-api/requirements.txt
```

## Run

```bash
PYTHONPATH=. uvicorn api:app --app-dir apps/analyzer-api --host 127.0.0.1 --port 8000 --reload
```

## Environment

- `ANALYZER_AUDIO_ROOT`:
  relative to repo root by default (`audiosToTest`), or absolute path.
- `ANALYZER_CORS_ORIGINS`:
  comma-separated origins for CORS (default:
  `http://localhost:3000,http://127.0.0.1:3000`).
