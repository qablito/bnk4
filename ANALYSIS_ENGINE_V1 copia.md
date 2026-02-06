# BeetsNKeys — Analysis Engine v1

**Status:** Stable Spec  
**Audience:** Product, Engineering, Audio Analysis  
**Scope:** Audio analysis engine (server-side), no UI  
**Language:** English (UI i18n handles ES rendering)

---

## 0. Scope & Principles

### 0.1 Objective
Provide a dual-purpose audio analysis engine:
- **DJ / Creator basic mode:** fast, reliable BPM + Key/Mode detection
- **Engineering / Pro mode:** deep technical insight for DAW, mixing, and production workflows

### 0.2 Non-Goals (v1)
- No automatic creative decisions
- No macro song structure labeling (verse/chorus/etc.)
- No DAW-side automation execution
- No subjective aesthetic judgments (v1 is neutral)

### 0.3 Precision Contract (Summary)
Every metric:
- MAY include `confidence ∈ [0.0, 1.0]`
- MAY include `candidates[]`
- MUST omit itself entirely if confidence is below minimum threshold
- MUST prefer omission over low-quality data

### 0.4 Gating by Role (Global)
| Role  | Visibility |
|------|------------|
| Guest | BPM, Key+Mode only |
| Free  | Most metrics, limited depth |
| Pro   | Full metrics, events, exports |

Locked metrics MUST be returned as objects with `locked: true` to enable UI upsell without extra calls.

---

## 1. Pipeline Overview

### 1.1 Ingest
- Validate format & size per role
- Decode audio
- Reject unsupported formats early

### 1.2 Pre-processing
- Loudness normalization (analysis-only)
- Resampling to internal reference SR
- Channel analysis (mono + stereo)

### 1.3 Feature Extraction
Executed per block:
- Tempo & grid
- Tonal analysis
- Loudness & dynamics
- Spectral balance
- Stereo & phase
- Events (clipping, silence, noise)

### 1.4 Aggregation
- Candidate ranking
- Confidence computation
- Stability analysis
- Event consolidation (ranges)

### 1.5 Post-processing
- Grid snapping (v1)
- Rounding (DJ-friendly)
- Warning generation

### 1.6 Packaging
- Role-based gating
- Locked fields
- Unlock hints
- Export preparation

---

## 2. Core Metrics (DJ Basic)
### 2.1 BPM
#### Output
```json
{
  "bpm": {
    "value_exact": 69.8,
    "value_rounded": 70,
    "confidence": 0.83,
    "candidates": [
      { "value": 70, "rank": 1 },
      { "value": 140, "rank": 2 }
    ]
  }
}
```

**Rules**
	•	value_rounded shown as primary
	•	value_exact available for advanced users
	•	Half/double candidates ONLY if delta score ≤ threshold
	•	Guest sees only rounded value

**TODO v2**
	•	Intelligent DAW grid snapping
	•	Full warp map (Pro)

### 2.2 Key + Mode
#### Output
```json
{
  "key_mode": {
    "value": "F# minor",
    "confidence": 0.81,
    "candidates": [
      { "value": "F# minor", "rank": 1 },
      { "value": "A major", "rank": 2 }
    ]
  }
}
```
**Rules**
	•	Always combined as key_mode
	•	Only Major / Minor in v1
	•	Extended modes ONLY if strong evidence (v2)

**Autotune**
	•	Autotune Setup Pack derived from key_mode
	•	Guest sees key_mode but autotune pack is locked

### 3. Grid & Groove
#### Output
```json
{
  "grid": {
    "confidence": 0.42,
    "offset_seconds": 0.03,
    "warning": "low_confidence"
  }
}
```

**Rules**
	•	First usable downbeat
	•	If confidence low: show warning or omit
	•	Guest: locked preview only

**TODO v2**
	•	Full warp markers
	•	Groove templates

### 4. Loudness & Dynamics
**Metrics**
	•	LUFS-I (Integrated)
	•	LUFS-M (Momentary, aggregate)
	•	True Peak
	•	Crest Factor / PLR

#### Output
```json
{
  "loudness": {
    "lufs_i": -8.1,
    "true_peak_dbtp": 0.3,
    "crest_factor": 7.2
  }
}
```

#### Recomendations (Pro)
```json
{
  "recording_headroom": {
    "target_lufs_i": -18,
    "recommended_gain_reduction_db": -9.9,
    "vocal_starting_gain_db": -12
  }
}
```

***TODO v2***
	•	Sliding windows
	•	Percentiles (p95)

### 5. Stereo & Channels
#### Output
```json
{
  "stereo": {
    "rating": "issues_detected",
    "mono_collapse_loss_db": -3.4,
    "events": [
      { "start": 12.3, "end": 18.1 }
    ]
  }
}
```
**Rules**
	•	Numbers hidden in Free
	•	Badges preferred in v1

### 6. Clipping & True Peak
#### Output
```json
{
  "clipping": {
    "sample_clipping_events": [
      { "start": 0.11, "end": 0.13 }
    ],
    "true_peak_exceedance_events": [
      { "start": 45.2, "end": 45.9 }
    ]
  }
}
```
**Rules**
	•	Continuous ranges only
	•	No microsecond spam

### 7. Spectral Balance
**Bands**
	•	sub, bass, low-mid, mid, high-mid, presence, air

#### Output
```json
{
  "spectral_balance": {
    "bands": {
      "bass": -2.1,
      "mid": 0.3,
      "air": 1.8
    }
  }
}
```

### 8. Tonality & Harmonic Context
#### Output
```json
{
  "tonality": {
    "confidence": 0.78,
    "stability": 0.65,
    "drift_events": [
      { "start": 90.1, "end": 102.4 }
    ]
  }
}
```
**Relations**
	•	Parallel
	•	Relative
	•	Dominant
	•	Subdominant

**Compatible Keys**
	•	Free: top-8
	•	Pro: top-12

**TODO v2**
	•	Camelot confidence

### 9. Sections & Markers
#### Output
```json
{
  "sections": [
    {
      "start": 32.0,
      "end": 64.0,
      "energy_delta": 0.42
    }
  ]
}
```
**Rules***
	•	No labels
	•	Energy-based
	•	Guest: locked

### 10. Onsets / Transients
#### Output
```json
{
  "onsets": {
    "density": "high",
    "events": [
      { "start": 12.0, "end": 18.0 }
    ]
  }
}
```

### 11. Silence & Low-Energy
#### Output
```json
{
  "silence": {
    "real_silence_events": [],
    "low_energy_usable_events": [
      { "start": 0.0, "end": 6.4 }
    ]
  }
}
```

### 12. Noise / Hum / Hiss
#### Output
```json
{
  "noise": {
    "noise_floor_dbfs": -58,
    "hiss_detected": true,
    "hum_detected": false
  }
}
```

### 13. Structure (Energy Phases)
#### Output
```json
{
  "energy_phases": [
    { "start": 0.0, "end": 42.1 },
    { "start": 42.1, "end": 86.3 },
    { "start": 86.3, "end": 130.0 }
  ]
}
```

### 14. Exports & DAW Pack
**Formats**
	•	analysis.json (Free/Pro)
	•	metadata.json (Free)
	•	markers.json / csv (Free preview 3)
	•	ableton_markers.json (v1)
	•	report.pdf (Free watermark / Pro full)

**Guest**: no exports.

### 15. Errors & Warnings
	•	Normalized JSON
	•	Block-level warning codes
	•	Omit > warn > lock priority

### 16. Performance & Limits
Role    Size    Time
Guest   3 MiB   2.1s
Free    8 MiB   3.4s
Pro     100 MiB 15min

### 17. Security Notes
**See:**
	•	SECURITY_SPEC.md
	•	CONTRACTS/

### 18. TODOs v2 (Pro)
	•	Modal key detection
	•	Full warp maps
	•	Camelot confidence
	•	Sliding loudness
	•	Autotune presets per style
	•	Structure labeling
