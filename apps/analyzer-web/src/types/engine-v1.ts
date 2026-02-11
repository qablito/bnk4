/** Roles supported by Engine v1 packaging. */
export type Role = "guest" | "free" | "pro";

/** Confidence levels emitted by Engine v1. */
export type Confidence = "low" | "medium" | "high";

// ---------------------------------------------------------------------------
// Track
// ---------------------------------------------------------------------------
export interface TrackInfo {
  duration_seconds: number;
  sample_rate_hz: number;
  channels: number;
  format: string;
  codec?: string | null;
  container?: string | null;
}

// ---------------------------------------------------------------------------
// BPM
// ---------------------------------------------------------------------------
export interface BPMCandidate {
  value: { value_rounded: number; value_exact?: number };
  rank: number;
  score: number;
  relation: string;
}

export interface BPMAdvancedCandidate {
  candidate_bpm: number;
  candidate_family: string;
  candidate_score: number;
}

export interface BPMValue {
  value_exact: number;
  value_rounded: number;
}

export interface BPMMetric {
  confidence: Confidence;
  method: string;
  limits?: string;
  value?: BPMValue;
  candidates?: BPMCandidate[];
  /** Advanced fields (free/pro only, stripped for guest). */
  bpm_raw?: number | null;
  bpm_raw_confidence?: string;
  bpm_reportable?: number | null;
  bpm_reportable_confidence?: string;
  timefeel?: string;
  bpm_reason_codes?: string[];
  bpm_candidates?: BPMAdvancedCandidate[];
}

// ---------------------------------------------------------------------------
// Key / Mode
// ---------------------------------------------------------------------------
export interface KeyCandidate {
  key: string;
  mode: string | null;
  score: number;
  family: string;
  rank: number;
}

export interface KeyModeMetric {
  value: string | null;
  mode: string | null;
  confidence?: Confidence;
  reason_codes?: string[];
  candidates?: KeyCandidate[];
  method?: string;
}

// ---------------------------------------------------------------------------
// Events (free/pro only)
// ---------------------------------------------------------------------------
export interface AnalysisEvents {
  clipping?: { sample_clipping_ranges: unknown[]; true_peak_exceedance_ranges: unknown[] };
  stereo?: { stereo_issue_ranges: unknown[] };
  tonality?: { tonal_drift_ranges: unknown[] };
  noise?: { noise_change_ranges: unknown[] };
}

// ---------------------------------------------------------------------------
// Top-level output
// ---------------------------------------------------------------------------
export interface AnalysisOutput {
  engine: { name: string; version: string };
  analysis_id: string;
  created_at: string;
  role: Role;
  track: TrackInfo;
  metrics: {
    bpm?: BPMMetric;
    key?: KeyModeMetric;
    key_mode?: KeyModeMetric;
  };
  events?: AnalysisEvents | Record<string, never>;
  warnings?: string[];
}

// ---------------------------------------------------------------------------
// Type guards
// ---------------------------------------------------------------------------
export function isAnalysisOutput(v: unknown): v is AnalysisOutput {
  if (typeof v !== "object" || v === null) return false;
  const o = v as Record<string, unknown>;
  return (
    typeof o.analysis_id === "string" &&
    typeof o.role === "string" &&
    typeof o.track === "object" &&
    typeof o.metrics === "object"
  );
}

export function hasBPM(metrics: AnalysisOutput["metrics"]): metrics is AnalysisOutput["metrics"] & { bpm: BPMMetric } {
  return metrics.bpm !== undefined;
}

export function hasKey(metrics: AnalysisOutput["metrics"]): metrics is AnalysisOutput["metrics"] & { key: KeyModeMetric } {
  return metrics.key !== undefined;
}
