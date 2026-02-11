# Engine v1 Contract (Public)

This document freezes the public output contract for Engine v1.

Scope:
- Global BPM (raw + reportable)
- Global Key/Mode
- Metadata only (no loudness, no section-level tonality, no Camelot)

Rules:
- Key may be emitted while mode is withheld.
- If mode is withheld, output MUST include `mode: null` and reason code
  `mode_withheld_insufficient_evidence` (free/pro only).
- Guest output must not include candidates, confidence, or reason_codes.
- Ordering is deterministic: reason_codes and candidates are stable.

## Example A: Key + Mode Emitted (Free/Pro)

```json
{
  "role": "pro",
  "track": {
    "duration_seconds": 198.4,
    "sample_rate_hz": 44100,
    "channels": 2,
    "format": "mp3"
  },
  "metrics": {
    "key": {
      "value": "A",
      "mode": "minor",
      "confidence": "high",
      "reason_codes": ["emit_confident"],
      "candidates": [
        {"key": "A", "mode": "minor", "score": 0.82, "family": "direct", "rank": 1},
        {"key": "C", "mode": "major", "score": 0.41, "family": "direct", "rank": 2}
      ],
      "method": "key_mode_global_v1"
    }
  }
}
```

## Example B: Key Emitted, Mode Withheld (Free/Pro)

```json
{
  "role": "pro",
  "metrics": {
    "key": {
      "value": "A",
      "mode": null,
      "confidence": "medium",
      "reason_codes": [
        "mode_withheld_insufficient_evidence",
        "emit_consistent_weak_evidence"
      ],
      "candidates": [
        {"key": "A", "mode": null, "score": 0.73, "family": "key_aggregate", "rank": 1},
        {"key": "B", "mode": null, "score": 0.27, "family": "key_aggregate", "rank": 2}
      ],
      "method": "key_mode_global_v1"
    }
  }
}
```

## Example C: Full Omit (Free/Pro)

```json
{
  "role": "pro",
  "metrics": {
    "key": {
      "value": null,
      "mode": null,
      "confidence": "low",
      "reason_codes": ["omitted_low_confidence"],
      "candidates": [
        {"key": "A", "mode": "minor", "score": 0.25, "family": "direct", "rank": 1},
        {"key": "C", "mode": "major", "score": 0.25, "family": "direct", "rank": 2}
      ],
      "method": "key_mode_global_v1"
    }
  }
}
```

## Example D: Guest-Safe Output

```json
{
  "role": "guest",
  "metrics": {
    "key": {
      "value": "A",
      "mode": null
    },
    "key_mode": {
      "value": "A",
      "mode": null
    }
  }
}
```
