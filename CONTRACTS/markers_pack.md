# Markers Pack Contract (Engine v1)

This contract defines the export marker pack format produced by Engine v1.

Scope:
- Marker metadata only. No DAW project generation.
- Pack is designed to be converted by clients/tools into DAW-specific formats.

Role gating:
- Guest: no exports.
- Free: preview pack only (maximum 3 markers).
- Pro: full pack.

## 1. Pack Container
`markers_pack.zip` contains:
- `manifest.json`
- `markers.json`
- `markers.csv` (optional convenience)
- `ableton_markers.json` (v1 adapter metadata for Ableton import tooling)

## 2. Manifest
`manifest.json`:
```json
{
  "engine_version": "v1",
  "analysis_id": "uuid",
  "created_at": "rfc3339",
  "track": {
    "duration_seconds": 123.45
  },
  "limits": {
    "max_markers": 3
  }
}
```

`limits.max_markers` MUST reflect role gating (Free preview vs Pro).

## 3. Canonical Markers List
`markers.json`:
```json
{
  "markers": [
    {
      "time_seconds": 42.1,
      "type": "downbeat",
      "label": "Downbeat"
    }
  ]
}
```

Marker fields:
- `time_seconds` (number): must satisfy `0 <= time_seconds <= track.duration_seconds`
- `type` (string enum): `downbeat` | `grid_anchor` | `energy_phase` | `warning`
- `label` (string): UI-friendly label (English)

Rules:
- Markers MUST be sorted ascending by `time_seconds`.
- Markers MUST be deduplicated: two markers with the same `type` and `time_seconds` are not allowed.

## 4. CSV (Optional)
`markers.csv` columns:
- `time_seconds,type,label`

## 5. Ableton Adapter Metadata (v1)
`ableton_markers.json` is an adapter input for an external tool that maps canonical markers to an Ableton Live set.

Shape:
```json
{
  "adapter": "ableton",
  "version": "v1",
  "markers_source": "markers.json"
}
```

Rules:
- This file does not represent an Ableton project. It only declares conversion intent.

