# Analysis Output Contract (Engine v1)

This contract defines the canonical analysis JSON shape and role gating semantics. It is normative for future implementation.

References:
- Engine spec: `ANALYSIS_ENGINE_V1.md`
- Security invariants and error model: `SECURITY_SPEC.md`
- Precision Contract schema: `CONTRACTS/precision_contract.schema.json`

## 1. Top-Level Shape

```json
{
  "engine": { "name": "bnk-analysis-engine", "version": "v1" },
  "analysis_id": "uuid",
  "created_at": "rfc3339",
  "role": "guest",
  "track": {
    "duration_seconds": 123.45,
    "format": "wav",
    "sample_rate_hz": 44100,
    "channels": 2
  },
  "metrics": {},
  "events": {
    "clipping": {
      "sample_clipping_ranges": [],
      "true_peak_exceedance_ranges": []
    },
    "stereo": {
      "stereo_issue_ranges": []
    },
    "tonality": {
      "tonal_drift_ranges": []
    },
    "noise": {
      "noise_change_ranges": []
    }
  },
  "warnings": []
}
```

Rules:
- `metrics` is an object keyed by metric name.
- `events` is structured by category and reserved for range-based events (Pro only unless stated). Guests MUST receive `events: {}` or omit `events`.
- `warnings` is an array of warning objects; omit if empty.

## 2. Metric Variants

### 2.1 Unlocked metric (Precision Contract)
Unlocked metrics MUST follow the Precision Contract shape:
- `value` (optional if ambiguous)
- `confidence` (required)
- `candidates` (required when `confidence` is below the threshold defined by the metric)
- `method` (required)
- `limits` (required)

Optional:
- `evidence` (structured, omitted when empty)

### 2.2 Locked metric (Upsell-safe)
Locked metrics MAY appear when:
- The metric is restricted by role, and
- There is real evidence that the metric would be meaningful if unlocked.

Locked shape:
```json
{
  "locked": true,
  "unlock_hint": "Upgrade to unlock this metric.",
  "preview": {}
}
```

Rules:
- If `locked: true`, the block MUST NOT include numeric `confidence` for any role.
- Locked metrics MUST NOT include `evidence` for Guest.
- Locked metrics MUST omit `value`, `confidence`, and `candidates` unless the engine spec explicitly allows a safe preview.
- `preview` MUST be omitted when empty.

### 2.3 Omitted metric
Metrics MUST be omitted when:
- Not applicable, or
- Confidence is below the minimal usefulness threshold, or
- Evidence is too weak to justify even a locked preview for that role.

## 3. Candidates Semantics by Role

Candidates are role-sensitive:
- Guest candidates are allowed only as ranked values:
  - Allowed fields: `value`, `rank`
  - Disallowed: per-candidate `confidence`, `score`, ambiguity labels, `evidence`
- Guest candidates are only allowed for `metrics.bpm` and `metrics.key_mode` when those metrics are present and unlocked.
- Free candidates may include per-candidate `confidence` or `score` where specified (for tonal metrics).
- Pro may include per-candidate evidence (compact) where specified.

## 4. Evidence Rules
- Evidence MUST be absent if empty.
- Guest: evidence is always omitted.
- Free: evidence may be included but must be compact and structured (no raw audio).
- Pro: evidence may be included per metric; event ranges go in `events`, not inline micro-events.

## 5. Events (Ranges)
Standard range object shape:
```json
{
  "start_s": 12.3,
  "end_s": 18.1,
  "severity": "high"
}
```

Rules:
- Ranges are `[start_s, end_s)` with `end_s > start_s`.
- Events MUST be consolidated (no per-frame spam).
- Guests get no events.

Storage paths (structured by category, no free-form `kind`):
- `events.clipping.sample_clipping_ranges[]`
- `events.clipping.true_peak_exceedance_ranges[]`
- `events.stereo.stereo_issue_ranges[]`
- `events.tonality.tonal_drift_ranges[]`
- `events.noise.noise_change_ranges[]`

## 6. Locked vs Omitted: Decision Priority
Priority order for any metric:
1. Omit (if low quality)
2. Include unlocked (if allowed by role)
3. Include locked (only if meaningful and allowed by the engine spec)

## 7. Exports (References Only)
Exports are not embedded in analysis output. See:
- `CONTRACTS/export_signing.md` (auth-gated download)
- `CONTRACTS/export_sharing.md` (reserved, bearer share links)
- `CONTRACTS/markers_pack.md` (markers pack format)
