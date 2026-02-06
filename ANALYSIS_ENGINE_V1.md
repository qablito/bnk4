# BeetsNKeys (bnk4) Analysis Engine v1 (Normative Spec)

**Status:** Stable Spec (v1)  
**Audience:** Product, Engineering, Audio Analysis  
**Scope:** Engine behavior and outputs only (no implementation)  
**Language:** English

## 0. Non-Negotiables
- This spec defines the *canonical* analysis output for Engine v1.
- Security invariants and normalized error model are defined in `SECURITY_SPEC.md` and are normative.
- Precision Contract schema is defined in `CONTRACTS/precision_contract.schema.json` and is normative.
- Omit low-quality metrics rather than returning misleading values.
- `bpm` and `key_mode` MUST be omitted (not locked) when they are unreliable or not analyzable, for all roles including Guest.
- Guest output must be minimal: only show unlocked content that has real evidence.

## 1. Terms
- **Metric block:** a top-level entry in `metrics` (for example `bpm`, `key_mode`, `grid`).
- **Unlocked metric:** metric block contains usable values for the caller role.
- **Locked metric:** metric block is present but contains `locked: true`; values are restricted or absent.
- **Omitted metric:** metric block is absent (quality too low, not applicable, or intentionally hidden).
- **Evidence:** structured support data for a metric (signals, counts, segments). Evidence is optional and must be omitted when empty.
- **Event range:** consolidated time range `[start_s, end_s)` describing a condition (clipping, drift, noise, etc.).

Role glossary:
- **Guest:** device-bound guest session, limited visibility.
- **Free:** authenticated user on free tier.
- **Pro:** authenticated user on pro tier.

## 2. Pipeline (Conceptual)
The engine is defined as a deterministic pipeline. Implementations may differ internally, but outputs must match this contract.

1. **Ingest**
   - Validate input size/format (see `SECURITY_SPEC.md` UPLOAD invariants).
   - Decode audio to an internal PCM representation.
2. **Pre-processing**
   - Resample to internal reference sample rate (tunable).
   - Normalize analysis gain (analysis-only, not persisted).
   - Compute mono and stereo representations.
3. **Feature extraction**
   - Tempo and beat grid features.
   - Tonal features (pitch class energy, chroma stability).
   - Loudness and dynamics features (LUFS, peaks).
   - Spectral and stereo features.
   - Raw events (micro-events) for clipping, true peak exceedance, noise changes, stereo issues, tonal drift.
4. **Aggregation**
   - Candidate ranking (tempo, key/mode).
   - Confidence computation per metric.
   - Consolidate raw events into ranges (Section 8).
5. **Packaging**
   - Apply role gating and locking/omission rules (Section 4).
   - Attach warnings (without leaking secrets or audio content).
   - Produce canonical JSON output (Section 3, plus `CONTRACTS/analysis_output.md`).

## 3. Canonical Output (Top Level)
Canonical output is a JSON object with these top-level keys:

```json
{
  "engine": {
    "name": "bnk-analysis-engine",
    "version": "v1"
  },
  "analysis_id": "uuid",
  "created_at": "2026-02-06T00:00:00Z",
  "role": "guest",
  "track": {
    "duration_seconds": 123.45,
    "format": "wav",
    "sample_rate_hz": 44100,
    "channels": 2
  },
  "metrics": {},
  "events": {},
  "warnings": []
}
```

Rules:
- `metrics` contains per-metric blocks (unlocked or locked). Omitted metrics are absent.
- `events` is structured by category and contains event ranges for Pro only (unless explicitly allowed for Free). Guests get no event ranges and MUST receive `events: {}` or omit `events`.
- `warnings` are short codes with optional structured details; omit if empty.
- Do not include raw audio, waveforms, or any audio blobs. (See `SECURITY_SPEC.md` DATA invariants.)

See `CONTRACTS/analysis_output.md` for gating semantics and the locked/omitted rules.

## 4. Role Gating and Lock/Omit Rules

### 4.1 Global rules
- If a metric is low quality and not minimally usable, it MUST be omitted for all roles.
- `bpm` and `key_mode` MUST NOT be returned as locked previews when omitted for quality.
- Tunables (defaults):
  - `bpm_min_confidence_omit`: 0.35
  - `key_mode_min_confidence_omit`: 0.45
- If a metric is *potentially useful* but restricted by role:
  - It MAY be returned as `locked: true` only when there is real evidence and the preview is meaningful.
  - If evidence is weak or empty, omit rather than returning a noisy locked block.
- Evidence/reasons:
  - MUST be absent if empty.
  - Guest: evidence is always omitted. (No reasons, no evidence.)
  - Free: evidence may be included but must be compact and structured.
  - Pro: evidence and event ranges may be included per metric definitions.

### 4.2 Guest rules (strict)
- Unlocked metrics:
  - `bpm` (only `value_rounded`)
  - `key_mode` (value like `F# minor`)
- All other metrics:
  - Return as locked blocks only when the preview would be meaningfully correct.
  - Do not include candidate scores, per-candidate confidences, ambiguity labels, or evidence.
  - Candidates are allowed only as ranked values (no scores), and only for `bpm` and `key_mode`.

### 4.3 Free rules
- Unlocked: most metrics, but limited depth and reduced numeric clutter in certain blocks.
- Tonal candidates (`key_mode` candidates and compatible keys) may include confidence/score metadata.
- Exports allowed with watermark/capped metrics (Section 9).

### 4.4 Pro rules
- Full depth: events, drift, detailed packs, full exports, and expanded lists (for example compatible keys top-12).
- v1.5 reserved additions are documented as TODOs (Section 10) and must not appear unless the spec is bumped.

## 5. Metric Blocks (v1)
All metric blocks use one of these shapes:
- **Unlocked metric:** follows the Precision Contract: `value`, `confidence`, `candidates` (when required), `method`, `limits`.
- **Locked metric:** `locked: true`, `unlock_hint`, and optional safe `preview` (role-specific). No evidence for guests.

### 5.1 BPM (`metrics.bpm`)

Unlocked (Free/Pro) shape:
```json
{
  "value": {
    "value_exact": 69.8,
    "value_rounded": 70
  },
  "confidence": 0.83,
  "candidates": [
    { "value": { "value_rounded": 70 }, "rank": 1 },
    { "value": { "value_rounded": 140 }, "rank": 2 }
  ],
  "method": "tempo_estimation_v1",
  "limits": "Fails on non-percussive material or extreme tempo drift."
}
```

Guest behavior:
- Unlocked: only `value.value_rounded`.
- `value.value_exact` MUST be omitted for Guest.
- If `confidence < bpm_min_confidence_omit` or tempo is not analyzable, `metrics.bpm` MUST be omitted (not locked) for all roles.

Half/double candidate rule (tunable):
- Compute internal candidate scores `s1 >= s2`.
- Only include half/double candidate (2x or 0.5x) if `s1 - s2 <= tempo_half_double_delta_max`.
- Default `tempo_half_double_delta_max`: 0.08.

Rounding rule:
- v1 uses `round()` for `value_rounded`. (TODO v2: grid-aware snapping.)

### 5.2 Key+Mode (`metrics.key_mode`)
Value format:
- English note spelling (A, Bb, F#, etc.)
- Mode is exactly `major` or `minor`.
- Example: `F# minor`, `A major`.

Unlocked shape:
```json
{
  "value": "F# minor",
  "confidence": 0.81,
  "candidates": [
    { "value": "F# minor", "rank": 1 },
    { "value": "A major", "rank": 2 }
  ],
  "method": "key_mode_estimation_v1",
  "limits": "Can be ambiguous on atonal, heavily percussive, or modulating content."
}
```

Guest candidate restriction:
- Candidates MUST be ranked values only (`value`, `rank`).
- No per-candidate scores/confidence.
- If `confidence < key_mode_min_confidence_omit` or tonality is not analyzable, `metrics.key_mode` MUST be omitted (not locked) for all roles.

Extended modes (dorian, phrygian, etc.):
- v1: MUST NOT appear.
- v2 TODO: may appear only when evidence is strong; otherwise omit them entirely (no candidates).

Camelot:
- v1: derived from `key_mode.value` for Free/Pro. No separate confidence.
- v2 TODO: `camelot_confidence` as an independent metric.

### 5.3 Compatible Keys (`metrics.compatible_keys`)
Derived from `key_mode.value`.

Relations (v1):
- `parallel`, `relative`, `dominant`, `subdominant`

Free:
- top-8 keys

Pro:
- top-12 keys

Shape (Free/Pro):
```json
{
  "value": [
    { "key_mode": "A major", "relation": "relative" },
    { "key_mode": "E minor", "relation": "dominant" }
  ],
  "confidence": 0.7,
  "method": "compatible_keys_v1",
  "limits": "Assumes stable tonality; may be misleading on modulating tracks."
}
```

Guest:
- Omit or lock (no list values) depending on evidence quality.

v2 TODO:
- Modal interchange.

### 5.4 Autotune Setup Pack (`metrics.autotune_setup_pack`)
This replaces any redundant `autotune_hint`. It is a *starting point* pack (not creative taste).

Unlocked (Free/Pro) shape:
```json
{
  "value": {
    "input_type_suggestion": "tenor",
    "retune_speed_range_ms": [15, 45],
    "humanize_range": [0.2, 0.6],
    "key_mode_source": "key_mode"
  },
  "confidence": 0.6,
  "method": "autotune_setup_pack_v1",
  "limits": "Starting point only; does not predict stylistic intent."
}
```

Guest:
- Always `locked: true` (no values). Include `unlock_hint`.

v1.5 reserved (Pro-only, not implemented):
- Style-based autotune preset suggestion only when evidence is strong.

### 5.5 Grid / Groove (`metrics.grid`)
v1 fields:
- `confidence`
- `offset_seconds` (grid offset to align beats)
- `downbeat_seconds` (first usable downbeat)

Unlocked shape:
```json
{
  "value": {
    "offset_seconds": 0.03,
    "downbeat_seconds": 1.12
  },
  "confidence": 0.72,
  "method": "grid_estimation_v1",
  "limits": "Low confidence on rubato or heavy swing; may misplace downbeats."
}
```

Inclusion thresholds (tunables):
- `grid_min_confidence_omit`: 0.25 (below: omit)
- `grid_min_confidence_minimally_usable`: 0.45 (between omit and usable: include with warning)
- Guest locked preview allowed only if `confidence >= grid_guest_preview_min_confidence` (default 0.6).

Guest locked preview (when allowed):
```json
{
  "locked": true,
  "unlock_hint": "Upgrade to see beat grid details and marker packs.",
  "preview": {
    "downbeat_seconds": 1.12
  }
}
```

v2 TODO:
- Intelligent grid snapping (grid-aware, DAW-aligned).
- Full warp markers and groove templates.

### 5.6 Loudness & Dynamics (`metrics.loudness`)
Priorities:
- Always prioritize LUFS-I (integrated) as the primary loudness measure.
- LUFS-M is a supporting aggregate metric (not sliding windows in v1).

Unlocked shape:
```json
{
  "value": {
    "lufs_i": -8.1,
    "lufs_m": -7.2,
    "true_peak_dbtp": 0.3,
    "crest_factor_db": 7.2
  },
  "confidence": 0.85,
  "method": "loudness_dynamics_v1",
  "limits": "Full-track aggregate only; does not include percentiles or windows in v1."
}
```

True peak target reference (v1):
- Reference target: 0.0 dBTP.
- v2 TODO: allow -1.0 dBTP preset option.

### 5.7 Recording Headroom (Pro) (`metrics.recording_headroom`)
Pro-only in v1.

Rules:
- `target_lufs_i = -18` for beat.
- `recommended_gain_reduction_db = target_lufs_i - measured_lufs_i`
  - Negative means the beat is too loud and should be reduced.

Shape:
```json
{
  "value": {
    "target_lufs_i": -18,
    "recommended_gain_reduction_db": -9.9,
    "vocal_starting_gain_db": -12
  },
  "confidence": 0.7,
  "method": "recording_headroom_v1",
  "limits": "Starting point only; assumes typical vocal headroom needs."
}
```

v2 TODO:
- Preset bundles per genre/style when evidence is strong.
- Sliding windows and percentiles for loudness.

### 5.8 Stereo & Channels (`metrics.stereo`)
v1 required fields:
- `rating` (string enum, UI-friendly)
- `mono_collapse_loss_db`

Recommended rating enum:
- `good`, `ok`, `issues_detected`

Unlocked shape (Pro):
```json
{
  "value": {
    "rating": "issues_detected",
    "mono_collapse_loss_db": -3.4
  },
  "confidence": 0.7,
  "method": "stereo_analysis_v1",
  "limits": "Event ranges depend on correlation analysis; may miss subtle phase issues."
}
```

Free (minimal numeric clutter):
- `rating` is required.
- `mono_collapse_loss_db` MAY be rounded to 0.5 dB or omitted if not useful.

Pro events:
- Problem stereo regions returned in `events.stereo.stereo_issue_ranges` as consolidated ranges (Section 8).

### 5.9 Clipping & True Peak Events (`metrics.clipping`)
Separate conditions:
- `sample_clipping_events`
- `true_peak_exceedance_events`

Guest/Free:
- Locked or omitted depending on evidence quality.

Pro:
- Events returned as consolidated ranges under `events.clipping.*` (Section 8), not per-sample timestamps.

### 5.10 Spectral Balance (`metrics.spectral_balance`)
Bands (v1, 7 bands):
- `sub`, `bass`, `low_mid`, `mid`, `high_mid`, `presence`, `air`

Value definition:
- Each band value is `db_rel_total`: relative dB versus full-band total energy over the whole track.
- More negative means the band is quieter relative to the total.

Unlocked shape:
```json
{
  "value": {
    "bands_db_rel_total": {
      "sub": -18.0,
      "bass": -10.2,
      "low_mid": -8.1,
      "mid": -7.5,
      "high_mid": -9.2,
      "presence": -12.5,
      "air": -16.8
    }
  },
  "confidence": 0.75,
  "method": "spectral_balance_v1",
  "limits": "Aggregate only; does not model arrangement changes over time in v1."
}
```

### 5.11 Tonality / Stability / Drift (`metrics.tonality`)
v1 fields:
- `confidence` (tonality confidence)
- `tonal_stability` (0..1, higher is more stable)

Pro-only:
- `tonal_drift_ranges` in `events.tonality.tonal_drift_ranges` (Section 8).

Unlocked shape:
```json
{
  "value": {
    "tonal_stability": 0.65
  },
  "confidence": 0.78,
  "method": "tonality_stability_v1",
  "limits": "Drift events require stable pitch tracking; noisy material may reduce accuracy."
}
```

### 5.12 Noise / Hum / Hiss (`metrics.noise`)
v1 fields:
- `noise_floor_dbfs` (UI-friendly explanation: lower is quieter floor)
- `hiss_detected` (boolean)
- `hum_detected` (boolean)

Unlocked shape:
```json
{
  "value": {
    "noise_floor_dbfs": -58,
    "hiss_detected": true,
    "hum_detected": false
  },
  "confidence": 0.7,
  "method": "noise_detection_v1",
  "limits": "Detection depends on quiet segments; dense arrangements can mask noise."
}
```

Pro events:
- Noise change segments returned as `events.noise.noise_change_ranges`.

### 5.13 Energy Phases (`metrics.energy_phases`)
v1:
- No semantic labels (no verse/chorus).
- Minimum 3 phases.
- Returned as consolidated ranges with a coarse `energy_level` enum.

Guest:
- Locked only if the phases are meaningful (evidence strong).

Free:
- Unlocked but minimal.

Pro:
- Full with optional supporting evidence.

Shape (Free/Pro):
```json
{
  "value": [
    { "start_s": 0.0, "end_s": 42.1, "energy_level": "low" },
    { "start_s": 42.1, "end_s": 86.3, "energy_level": "mid" },
    { "start_s": 86.3, "end_s": 130.0, "energy_level": "high" }
  ],
  "confidence": 0.6,
  "method": "energy_phases_v1",
  "limits": "Energy phases are coarse and can miss short transitions."
}
```

## 6. Warnings (Engine v1)
Warnings are informational and must not leak evidence for guests.

Example warning object:
```json
{
  "code": "GRID_LOW_CONFIDENCE",
  "details": {
    "confidence": 0.31
  }
}
```

Guest:
- May receive only `code` without details.

## 7. Locked Blocks (Upsell Without Lying)
Locked blocks exist to support UI upsell, but must remain honest:
- Only include a locked block if the engine has enough evidence to believe the metric is meaningful.
- If `locked: true`, the block MUST NOT include:
  - Numeric `confidence`
  - `candidates` (including per-candidate scores/confidences)
  - `evidence`, reason codes, ambiguity labels, or explanations
- Locked blocks MUST NOT include evidence for guests.
- Locked blocks MAY include a small `preview` when explicitly allowed by the metric definition (for example `grid.preview.downbeat_seconds`).
- If `preview` is empty, it MUST be omitted.

## 8. Event Consolidation (Pro)
Raw detections must be consolidated into ranges:

Standard range object shape:
```json
{
  "start_s": 12.3,
  "end_s": 18.1,
  "severity": "high"
}
```

Storage paths (structured by category, no free-form `kind`):
- `events.clipping.sample_clipping_ranges[]`
- `events.clipping.true_peak_exceedance_ranges[]`
- `events.stereo.stereo_issue_ranges[]`
- `events.tonality.tonal_drift_ranges[]`
- `events.noise.noise_change_ranges[]`

Consolidation rules (tunables):
- Represent ranges as `[start_s, end_s)` with `end_s > start_s`.
- Sort by `start_s`, then merge adjacent ranges when the gap is <= `merge_gap_seconds` (default 0.10).
- Do not emit micro-ranges shorter than `min_range_seconds` unless the condition is critical (default 0.02).

No gaps logic:
- When a condition is continuously present, emit a single range.
- Do not emit per-sample timestamps or per-frame spam.

## 9. Exports and Packs (v1)
Exports are defined by security contracts:
- Export signing and downloads are auth-gated: `CONTRACTS/export_signing.md`.
- Guest cannot export.

Engine v1 export artifacts (conceptual):
- `analysis.json` (Free/Pro)
- `markers_pack.zip` (Free preview; Pro full)
- `report.pdf` (Free watermark + capped metrics; Pro full)

Markers packs are defined in `CONTRACTS/markers_pack.md`.

Free export constraints:
- Watermark PDF.
- Cap metrics depth (no Pro-only events; reduce lists).
- Markers pack contains at most 3 markers.

## 10. TODOs (v2 / Pro)
These are explicitly out of v1 scope and must not appear in v1 outputs.

- Intelligent grid snapping (grid-aware, DAW-aligned) instead of `round()`-only behavior.
- Extended modes (dorian, etc.) only when evidence is strong.
- Independent `camelot_confidence`.
- Loudness sliding windows and percentiles.
- Style-based autotune presets (Pro-only) only when evidence is strong.
- Modal interchange in compatible keys.
- Advanced marker packs (more formats, richer metadata).

## References
- Security invariants and error model: `SECURITY_SPEC.md`
- Canonical output gating contract: `CONTRACTS/analysis_output.md`
- Precision Contract schema: `CONTRACTS/precision_contract.schema.json`
- Export signing (auth-gated): `CONTRACTS/export_signing.md`
- Reserved bearer share links: `CONTRACTS/export_sharing.md`
