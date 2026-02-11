import type { AnalysisOutput, Role } from "./engine-v1";

// ---------------------------------------------------------------------------
// Requests
// ---------------------------------------------------------------------------
export type AnalyzeRequest =
  | { role: Role; input: { kind: "sample_id"; sample_id: string } }
  | { role: Role; input: { kind: "url"; url: string } };

export interface AnalyzeUploadParams {
  role: Role;
  file: File;
}

// ---------------------------------------------------------------------------
// Responses
// ---------------------------------------------------------------------------
export interface SamplesResponse {
  samples: Array<{
    id: string;
    name: string;
    url: string;
    duration_seconds?: number;
  }>;
}

export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  result?: AnalysisOutput;
  error?: string;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------
export class APIError extends Error {
  public readonly status: number;
  public readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.code = code;
  }
}
