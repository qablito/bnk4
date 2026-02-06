# Checks

Minimal linting for security/spec artifacts.

## Run

```
python3 CHECKS/validate_threat_model.py
python3 CHECKS/validate_contracts.py
```

Expected output is a single OK line per script. Non-zero exit code indicates failure.
