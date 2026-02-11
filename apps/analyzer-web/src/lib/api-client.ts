import type {
  AnalyzeRequest,
  AnalyzeUploadParams,
  JobStatusResponse,
  SamplesResponse,
} from "@/types/api";
import { APIError } from "@/types/api";
import type { AnalysisOutput } from "@/types/engine-v1";

const BASE_URL =
  process.env.DEV_MOCK === "1"
    ? ""
    : process.env.NEXT_PUBLIC_ANALYZER_API_URL || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 10_000;
const POLL_INTERVAL_MS = 1_000;
const MAX_POLL_ATTEMPTS = 60;

async function fetchWithTimeout(
  url: string,
  init?: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    return res;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new APIError(0, "TIMEOUT", `Request timed out after ${timeoutMs}ms`);
    }
    throw new APIError(0, "NETWORK_ERROR", (err as Error).message);
  } finally {
    clearTimeout(timer);
  }
}

function parseErrorPayload(body: unknown, status: number, fallback: string) {
  const payload = body as Record<string, unknown>;
  let code = typeof payload?.code === "string" ? payload.code : "UNKNOWN";
  let message = fallback;

  if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
    const first = payload.detail[0] as Record<string, unknown>;
    if (typeof first?.msg === "string") {
      message = first.msg;
    } else {
      message = JSON.stringify(first);
    }
    if (status === 422 && code === "UNKNOWN") {
      code = "VALIDATION_ERROR";
    }
    return { code, message };
  }

  if (typeof payload?.detail === "string") {
    message = payload.detail;
  } else if (typeof payload?.message === "string") {
    message = payload.message;
  } else if (typeof payload?.error === "string") {
    message = payload.error;
  }

  if (status === 422 && code === "UNKNOWN") {
    code = "VALIDATION_ERROR";
  }

  return { code, message };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let code = "UNKNOWN";
    let message = res.statusText;
    try {
      const body = await res.json();
      ({ code, message } = parseErrorPayload(body, res.status, message));
    } catch {
      // body not JSON
    }
    throw new APIError(res.status, code, message);
  }
  return res.json() as Promise<T>;
}

/** Fetch available demo samples. */
export async function fetchSamples(): Promise<SamplesResponse> {
  const res = await fetchWithTimeout(`${BASE_URL}/samples`);
  return handleResponse<SamplesResponse>(res);
}

/** Submit an analysis job from JSON input (url or sample_id). */
export async function submitAnalysis(
  req: AnalyzeRequest
): Promise<AnalysisOutput | JobStatusResponse> {
  const payload =
    req.input.kind === "sample_id"
      ? { role: req.role, sample_id: req.input.sample_id }
      : { role: req.role, sample_url: req.input.url };

  const res = await fetchWithTimeout(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<AnalysisOutput | JobStatusResponse>(res);
}

/** Submit an analysis job via multipart upload. */
export async function submitAnalysisUpload(
  role: AnalyzeUploadParams["role"],
  file: File
): Promise<AnalysisOutput | JobStatusResponse> {
  const formData = new FormData();
  formData.append("role", role);
  formData.append("file", file);

  const res = await fetchWithTimeout(`${BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<AnalysisOutput | JobStatusResponse>(res);
}

/** Check job status. */
export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetchWithTimeout(`${BASE_URL}/jobs/${jobId}`);
  return handleResponse<JobStatusResponse>(res);
}

/** Full analysis flow: submit, then poll if async. */
export async function analyzeWithPolling(
  req: AnalyzeRequest | AnalyzeUploadParams,
  onStatus?: (status: JobStatusResponse) => void
): Promise<AnalysisOutput> {
  const initial =
    "file" in req
      ? await submitAnalysisUpload(req.role, req.file)
      : await submitAnalysis(req);

  // Immediate result (has analysis_id + metrics = AnalysisOutput).
  if ("analysis_id" in initial && "metrics" in initial) {
    return initial as AnalysisOutput;
  }

  // Async job — poll.
  const job = initial as JobStatusResponse;
  let attempts = 0;

  while (attempts < MAX_POLL_ATTEMPTS) {
    const status = await fetchJobStatus(job.job_id);
    onStatus?.(status);

    if (status.status === "completed" && status.result) {
      return status.result;
    }
    if (status.status === "failed") {
      throw new APIError(500, "JOB_FAILED", status.error || "Analysis failed");
    }

    attempts++;
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  throw new APIError(0, "POLL_TIMEOUT", "Analysis polling timed out");
}
