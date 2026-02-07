# BeetsNKeys Analysis Engine v1 - Evaluation Harness

Evaluation framework for measuring objective improvements to the analysis engine.

## Core Principle

**DO NOT LIE.** If the engine is uncertain, it must omit the final value and return candidates with confidence instead. This harness tracks **omit rate** explicitly.

## Quick Start

### Run Evaluation

```bash
# From repo root
PYTHONPATH=. python3 engine/eval/run_eval.py

# With custom fixtures
PYTHONPATH=. python3 engine/eval/run_eval.py --fixtures my_fixtures.csv

# Save JSON report
PYTHONPATH=. python3 engine/eval/run_eval.py --output results.json

# Limit to first N fixtures (for quick testing)
PYTHONPATH=. python3 engine/eval/run_eval.py --limit 5

# Fail if any audio file is missing
PYTHONPATH=. python3 engine/eval/run_eval.py --fail-on-missing-files
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--fixtures PATH` | `engine/eval/fixtures.csv` | Path to fixtures CSV |
| `--output PATH` | (stdout) | Save JSON report to file |
| `--role ROLE` | `pro` | Analysis role: guest, free, pro |
| `--limit N` | (all) | Limit number of fixtures to process |
| `--fail-on-missing-files` | (skip) | Error if any audio file missing |
| `--top-n N` | 20 | Number of worst BPM errors to report |

## CSV Schema

```csv
path,bpm_gt,key_gt,mode_gt,flags,notes
engine/eval/samples/trap/song.mp3,170,B,minor,"bpm_strict,key_strict,double_time_preferred","grid 85 BPM, reported 170"
engine/eval/samples/rnb/song.mp3,92,G,minor,"bpm_strict,key_strict","normal timefeel"
engine/eval/samples/reggaeton/song.mp3,,A,minor,"key_strict,ambiguous","no strict BPM"
```

### Required Columns

| Column | Type | Description |
|--------|------|-------------|
| `path` | string | Path to audio file (relative to repo root) |
| `bpm_gt` | float | Ground truth BPM (empty = no strict BPM metric) |
| `key_gt` | string | Ground truth key: C, C#, D, D#, E, F, F#, G, G#, A, A#, B |
| `mode_gt` | string | Ground truth mode: major, minor |
| `flags` | string | Comma-separated flags (see below) |
| `notes` | string | Free-form comments |

### Flags

| Flag | Meaning |
|------|---------|
| `bpm_strict` | Include in BPM MAE calculation |
| `key_strict` | Include in key/mode accuracy calculation |
| `ambiguous` | Multiple valid interpretations exist |
| `short_audio` | Less than ~30 seconds |
| `double_time_preferred` | User expects double-time BPM (e.g., 170 not 85) |

### Extra Columns (Preserved)

The loader accepts additional columns (e.g., `genre`, `bars`, `sections`, `drift`) and preserves them in `fixture.extra`.

### Comments

Lines starting with `#` are ignored. Empty rows are skipped.

## Output

### Text Report (stderr)

```
================================================================================
BeetsNKeys Analysis Engine v1 - Evaluation Report
================================================================================

Overall:
  Total fixtures: 14
  Successful runs: 12
  Failed runs: 0
  Skipped runs: 2

BPM Metrics (bpm_strict fixtures only):
  Total strict: 13
  Predicted: 11
  Omitted: 2
  MAE: 15.45 BPM
  Omit rate: 15.4%

Top 20 Worst BPM Errors:
--------------------------------------------------------------------------------
1. engine/eval/samples/trap/trap__170__Bminor__song.mp3
   GT: 170.0 BPM
   Predicted: 85 BPM
   Error: 85.0 BPM
   Candidates: [85, 170]
   Notes: grid 85 BPM (raw), reported 170
...
```

### JSON Report (stdout or file)

```json
{
  "overall": {
    "total_fixtures": 14,
    "successful_runs": 12,
    "failed_runs": 0,
    "skipped_runs": 2
  },
  "bpm": {
    "n_total_strict": 13,
    "n_predicted": 11,
    "n_omitted": 2,
    "mae": 15.45,
    "omit_rate": 0.154
  },
  "key_mode": {
    "n_total_strict": 0,
    "n_predicted": 0,
    "n_omitted": 0,
    "accuracy": null,
    "omit_rate": null
  },
  "top_bpm_errors": [
    {
      "path": "engine/eval/samples/trap/trap__170__Bminor__song.mp3",
      "bpm_gt": 170.0,
      "bpm_pred": 85,
      "abs_error": 85.0,
      "candidates": [85, 170],
      "notes": "grid 85 BPM (raw), reported 170"
    }
  ]
}
```

## Metrics Explained

### BPM Metrics (only `bpm_strict` fixtures)

- **MAE (Mean Absolute Error)**: Average absolute difference between predicted and ground truth BPM
  - Computed only on fixtures where BPM was predicted (not omitted)
- **Omit rate**: Percentage of strict fixtures where BPM was omitted
  - Higher omit rate = more conservative (honest about uncertainty)
  - Too high = feature is not useful enough
- **Top BPM errors**: Worst predictions sorted by absolute error

### Key/Mode Metrics (placeholder for future)

- **Accuracy**: Percentage of exact matches (both key AND mode correct)
- **Omit rate**: Percentage of strict fixtures where key/mode was omitted

## Files

```
engine/eval/
├── __init__.py              # Package exports
├── README.md                # This file
├── fixtures.csv             # Ground truth data
├── samples/                 # Audio files (not in git)
├── eval_types.py            # Dataclasses
├── loader.py                # CSV parsing
├── runner.py                # Analysis runner
├── metrics.py               # Metric computation
├── run_eval.py              # CLI entrypoint
├── test_loader.py           # Loader tests
├── test_metrics.py          # Metrics tests
└── test_integration.py      # Integration tests
```

## Running Tests

```bash
# Run all eval tests
pytest engine/eval/test_*.py -v

# Run specific test file
pytest engine/eval/test_metrics.py -v

# With coverage
pytest engine/eval/test_*.py --cov=engine.eval --cov-report=term-missing
```

## Workflow for Improving Engine

1. **Establish baseline**:
   ```bash
   PYTHONPATH=. python3 engine/eval/run_eval.py --output baseline.json
   ```

2. **Make improvements** to feature extractors (bpm_v1, key_mode_v1)

3. **Re-evaluate**:
   ```bash
   PYTHONPATH=. python3 engine/eval/run_eval.py --output improved.json
   ```

4. **Compare**:
   ```bash
   jq '.bpm.mae' baseline.json improved.json
   jq '.bpm.omit_rate' baseline.json improved.json
   ```

## Adding Fixtures

### Guidelines

1. **Path relative to repo root**: `engine/eval/samples/genre/filename.mp3`
2. **Use consistent naming**: `{genre}__{bpm}__{key}{mode}__{title}.mp3`
3. **Mark flags appropriately**:
   - `bpm_strict`: Only if you're confident about ground truth
   - `double_time_preferred`: For genres where double-time is the user expectation
   - `ambiguous`: When multiple interpretations are valid
4. **Add notes**: Explain any quirks (non-integer bars, tempo drift, etc.)

### Example

```csv
path,bpm_gt,key_gt,mode_gt,flags,notes
engine/eval/samples/trap/trap__170__Bminor__Test.mp3,170,B,minor,"bpm_strict,key_strict,double_time_preferred","grid 85 BPM (raw), reported 170; bars=104"
```

## Design Decisions

1. **`bpm_gt` is user-reported BPM**: For double-time genres, this is the tempo the user expects (e.g., 170 not 85)

2. **Empty `bpm_gt` means no strict metric**: The fixture still runs, but doesn't contribute to MAE

3. **Omit rate is a first-class metric**: High omit rate is acceptable if predictions are honest

4. **Skipped files are tracked separately**: Missing audio files don't count as failures

5. **Extra columns are preserved**: Add `genre`, `bars`, etc. without breaking loader

6. **No engine modifications**: This harness is read-only; feature extractors stay unchanged
