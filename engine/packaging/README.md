# Packaging

Responsibilities:
- Apply role gating (guest/free/pro)
- Apply lock vs omit rules
- Produce canonical JSON output

This is the only place allowed to:
- Lock metrics
- Omit metrics
- Attach warnings

## Local Development

Editable install (recommended):
```sh
python3 -m pip install -e ".[dev]"
```

If you are in a restricted/offline environment where build isolation cannot download build deps:
```sh
python3 -m pip install -e ".[dev]" --no-build-isolation
```

Run tests:
```sh
python3 -m pytest -q
```

Note: Engine v1 audio ingest/decoding is intentionally minimal and metadata-oriented; no heavy audio dependencies are used yet.
