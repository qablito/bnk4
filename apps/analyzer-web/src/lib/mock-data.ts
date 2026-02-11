import type { AnalysisOutput } from "@/types/engine-v1";

const baseTrack = {
  duration_seconds: 198.4,
  sample_rate_hz: 44100,
  channels: 2,
  format: "mp3",
};

const baseEngine = { name: "bnk-analysis-engine", version: "v1" };

/** Confident result: key + mode emitted, high confidence BPM. */
export const confidentResult: AnalysisOutput = {
  engine: baseEngine,
  analysis_id: "mock-confident-001",
  created_at: "2025-01-15T10:00:00Z",
  role: "pro",
  track: baseTrack,
  metrics: {
    bpm: {
      confidence: "high",
      method: "tempo_candidates_v1",
      value: { value_exact: 127.8, value_rounded: 128 },
      candidates: [
        { value: { value_rounded: 128 }, rank: 1, score: 0.92, relation: "normal" },
        { value: { value_rounded: 64 }, rank: 2, score: 0.41, relation: "half" },
        { value: { value_rounded: 256 }, rank: 3, score: 0.15, relation: "double" },
      ],
      bpm_raw: 127.8,
      bpm_raw_confidence: "high",
      bpm_reportable: 128,
      bpm_reportable_confidence: "high",
      timefeel: "normal",
      bpm_reason_codes: ["prefer_raw"],
      bpm_candidates: [
        { candidate_bpm: 128, candidate_family: "base", candidate_score: 0.92 },
        { candidate_bpm: 64, candidate_family: "half", candidate_score: 0.41 },
      ],
    },
    key: {
      value: "A",
      mode: "minor",
      confidence: "high",
      reason_codes: ["emit_confident"],
      candidates: [
        { key: "A", mode: "minor", score: 0.82, family: "direct", rank: 1 },
        { key: "C", mode: "major", score: 0.41, family: "direct", rank: 2 },
      ],
      method: "key_mode_global_v1",
    },
  },
  events: {
    clipping: { sample_clipping_ranges: [], true_peak_exceedance_ranges: [] },
    stereo: { stereo_issue_ranges: [] },
    tonality: { tonal_drift_ranges: [] },
    noise: { noise_change_ranges: [] },
  },
  warnings: [],
};

/** Mode withheld: key emitted but mode is null. */
export const modeWithheldResult: AnalysisOutput = {
  engine: baseEngine,
  analysis_id: "mock-withheld-002",
  created_at: "2025-01-15T10:01:00Z",
  role: "pro",
  track: baseTrack,
  metrics: {
    bpm: confidentResult.metrics.bpm,
    key: {
      value: "A",
      mode: null,
      confidence: "medium",
      reason_codes: ["mode_withheld_insufficient_evidence", "emit_consistent_weak_evidence"],
      candidates: [
        { key: "A", mode: null, score: 0.73, family: "key_aggregate", rank: 1 },
        { key: "B", mode: null, score: 0.27, family: "key_aggregate", rank: 2 },
      ],
      method: "key_mode_global_v1",
    },
  },
  events: confidentResult.events,
  warnings: [],
};

/** Ambiguous / low confidence: values omitted. */
export const ambiguousResult: AnalysisOutput = {
  engine: baseEngine,
  analysis_id: "mock-ambiguous-003",
  created_at: "2025-01-15T10:02:00Z",
  role: "pro",
  track: baseTrack,
  metrics: {
    bpm: {
      confidence: "low",
      method: "tempo_candidates_v1",
      candidates: [
        { value: { value_rounded: 120 }, rank: 1, score: 0.35, relation: "normal" },
        { value: { value_rounded: 80 }, rank: 2, score: 0.33, relation: "normal" },
      ],
      bpm_raw: 120,
      bpm_raw_confidence: "low",
      bpm_reportable: null,
      bpm_reportable_confidence: "low",
      timefeel: "unknown",
      bpm_reason_codes: ["omitted_low_confidence"],
      bpm_candidates: [
        { candidate_bpm: 120, candidate_family: "base", candidate_score: 0.35 },
        { candidate_bpm: 80, candidate_family: "base", candidate_score: 0.33 },
      ],
    },
    key: {
      value: null,
      mode: null,
      confidence: "low",
      reason_codes: ["omitted_low_confidence"],
      candidates: [
        { key: "A", mode: "minor", score: 0.25, family: "direct", rank: 1 },
        { key: "C", mode: "major", score: 0.25, family: "direct", rank: 2 },
      ],
      method: "key_mode_global_v1",
    },
  },
  events: confidentResult.events,
  warnings: [],
};

/** Guest-safe output: no confidence, candidates, or reason_codes. */
export const guestResult: AnalysisOutput = {
  engine: baseEngine,
  analysis_id: "mock-guest-004",
  created_at: "2025-01-15T10:03:00Z",
  role: "guest",
  track: baseTrack,
  metrics: {
    bpm: {
      confidence: "high" as never, // stripped client-side but present for typing
      method: "tempo_candidates_v1",
      value: { value_exact: 127.8, value_rounded: 128 },
    },
    key: {
      value: "A",
      mode: null,
    },
  },
  events: {},
  warnings: [],
};

/** Map scenario name -> mock result. */
export const mockScenarios: Record<string, AnalysisOutput> = {
  confident: confidentResult,
  "mode-withheld": modeWithheldResult,
  ambiguous: ambiguousResult,
  guest: guestResult,
};

export const mockSamples = [
  { id: "s1", name: "Confident Track", url: "mock://confident", duration_seconds: 198.4 },
  { id: "s2", name: "Mode Withheld Track", url: "mock://mode-withheld", duration_seconds: 198.4 },
  { id: "s3", name: "Ambiguous Track", url: "mock://ambiguous", duration_seconds: 198.4 },
  { id: "s4", name: "Guest Track", url: "mock://guest", duration_seconds: 198.4 },
];
