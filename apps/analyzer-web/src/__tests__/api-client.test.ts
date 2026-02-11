import { beforeEach, describe, expect, it, vi } from "vitest";

const BASE_URL = "http://localhost:8000";

beforeEach(() => {
  vi.restoreAllMocks();
  vi.resetModules();
  vi.stubEnv("DEV_MOCK", "0");
  vi.stubEnv("NEXT_PUBLIC_DEV_MOCK", "0");
  vi.stubEnv("NEXT_PUBLIC_ANALYZER_API_URL", BASE_URL);
});

async function importClient() {
  return await import("@/lib/api-client");
}

describe("api-client", () => {
  it("uses same-origin base URL when DEV_MOCK=1", async () => {
    vi.stubEnv("DEV_MOCK", "1");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ samples: [] }),
      })
    );

    const { fetchSamples } = await importClient();
    await fetchSamples();

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/samples");
  });

  it("uses same-origin base URL when NEXT_PUBLIC_DEV_MOCK=1", async () => {
    vi.stubEnv("NEXT_PUBLIC_DEV_MOCK", "1");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ samples: [] }),
      })
    );

    const { fetchSamples } = await importClient();
    await fetchSamples();

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/samples");
  });

  it("submits sample_id as JSON payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ analysis_id: "a1", metrics: {}, role: "pro", track: { duration_seconds: 1, sample_rate_hz: 44100, channels: 2, format: "wav" } }),
      })
    );

    const { submitAnalysis } = await importClient();
    await submitAnalysis({ role: "pro", input: { kind: "sample_id", sample_id: "s2" } });

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(`${BASE_URL}/analyze`);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(init.body))).toEqual({ role: "pro", sample_id: "s2" });
  });

  it("submits URL as JSON payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ analysis_id: "a2", metrics: {}, role: "pro", track: { duration_seconds: 1, sample_rate_hz: 44100, channels: 2, format: "wav" } }),
      })
    );

    const { submitAnalysis } = await importClient();
    await submitAnalysis({ role: "pro", input: { kind: "url", url: "https://x.test/t.mp3" } });

    const fetchMock = vi.mocked(fetch);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual({
      role: "pro",
      sample_url: "https://x.test/t.mp3",
    });
  });

  it("submits multipart form-data for file upload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ analysis_id: "a3", metrics: {}, role: "pro", track: { duration_seconds: 1, sample_rate_hz: 44100, channels: 2, format: "wav" } }),
      })
    );

    const { submitAnalysisUpload } = await importClient();
    const file = new File(["abc"], "clip.mp3", { type: "audio/mpeg" });
    await submitAnalysisUpload("pro", file);

    const fetchMock = vi.mocked(fetch);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.headers).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
    const fd = init.body as FormData;
    expect(fd.get("role")).toBe("pro");
    expect(fd.get("file")).toBe(file);
  });

  it("parses FastAPI 422 detail[].msg into APIError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        statusText: "Unprocessable Entity",
        json: () => Promise.resolve({ detail: [{ msg: "field required", loc: ["body", "file"] }] }),
      })
    );

    const { submitAnalysis } = await importClient();

    await expect(
      submitAnalysis({ role: "pro", input: { kind: "url", url: "https://x.test/t.mp3" } })
    ).rejects.toMatchObject({
      name: "APIError",
      status: 422,
      code: "VALIDATION_ERROR",
      message: "field required",
    });
  });

  it("polls until completion", async () => {
    let calls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.endsWith("/analyze")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ job_id: "job-1", status: "pending" }),
          });
        }
        calls += 1;
        if (calls === 1) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ job_id: "job-1", status: "processing" }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              job_id: "job-1",
              status: "completed",
              result: {
                analysis_id: "done",
                role: "pro",
                track: {
                  duration_seconds: 1,
                  sample_rate_hz: 44100,
                  channels: 2,
                  format: "wav",
                },
                metrics: {},
              },
            }),
        });
      })
    );

    const { analyzeWithPolling } = await importClient();
    const result = await analyzeWithPolling({
      role: "pro",
      input: { kind: "sample_id", sample_id: "s1" },
    });

    expect(result.analysis_id).toBe("done");
  });
});
