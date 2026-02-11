import { NextResponse } from "next/server";
import {
  confidentResult,
  mockScenarios,
  mockSamples,
} from "@/lib/mock-data";

type ScenarioKey = keyof typeof mockScenarios;

const SAMPLE_ID_TO_SCENARIO: Record<string, ScenarioKey> = {
  s1: "confident",
  s2: "mode-withheld",
  s3: "ambiguous",
  s4: "guest",
};

const SCENARIO_ORDER: ScenarioKey[] = ["confident", "mode-withheld", "ambiguous", "guest"];

function stableScenarioFromString(seed: string): ScenarioKey {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash + seed.charCodeAt(i)) % SCENARIO_ORDER.length;
  }
  return SCENARIO_ORDER[hash] || "confident";
}

function pickScenarioBySampleId(sampleId: string): ScenarioKey {
  if (SAMPLE_ID_TO_SCENARIO[sampleId]) {
    return SAMPLE_ID_TO_SCENARIO[sampleId];
  }
  return stableScenarioFromString(sampleId);
}

function pickScenarioByUrl(url: string): ScenarioKey {
  const byMockScheme = url.replace("mock://", "") as ScenarioKey;
  if (mockScenarios[byMockScheme]) {
    return byMockScheme;
  }

  const sample = mockSamples.find((s) => s.url === url);
  if (sample) {
    return pickScenarioBySampleId(sample.id);
  }

  return stableScenarioFromString(url);
}

function pickScenarioByFilename(fileName: string): ScenarioKey {
  const normalized = fileName.toLowerCase();
  if (normalized.includes("withheld") || normalized.includes("mode")) {
    return "mode-withheld";
  }
  if (normalized.includes("amb") || normalized.includes("uncertain")) {
    return "ambiguous";
  }
  if (normalized.includes("guest")) {
    return "guest";
  }
  return stableScenarioFromString(normalized);
}

function withRole(result: typeof confidentResult, role: unknown) {
  if (role === "guest" || role === "free" || role === "pro") {
    return { ...result, role };
  }
  return result;
}

function validationError(msg: string) {
  return NextResponse.json({ detail: [{ msg }] }, { status: 422 });
}

export async function POST(request: Request) {
  if (process.env.DEV_MOCK !== "1") {
    return NextResponse.json(
      { code: "NOT_FOUND", message: "Mock routes disabled" },
      { status: 404 }
    );
  }

  const contentType = request.headers.get("content-type") || "";

  try {
    if (contentType.includes("multipart/form-data")) {
      const formData = await request.formData();
      const role = formData.get("role");
      const file = formData.get("file");

      if (!(file instanceof File)) {
        return validationError("file is required");
      }

      const scenario = pickScenarioByFilename(file.name);
      return NextResponse.json(withRole(mockScenarios[scenario], role));
    }

    const body = (await request.json()) as Record<string, unknown>;

    const role = body.role;
    const input = body.input as Record<string, unknown> | undefined;

    let scenario: ScenarioKey | null = null;

    if (input?.kind === "sample_id" && typeof input.sample_id === "string") {
      scenario = pickScenarioBySampleId(input.sample_id);
    } else if (input?.kind === "url" && typeof input.url === "string") {
      scenario = pickScenarioByUrl(input.url);
    } else if (typeof body.sample_id === "string") {
      scenario = pickScenarioBySampleId(body.sample_id);
    } else if (typeof body.sample_url === "string") {
      scenario = pickScenarioByUrl(body.sample_url);
    }

    if (!scenario) {
      return validationError("sample_id, sample_url, or valid input.kind is required");
    }

    return NextResponse.json(withRole(mockScenarios[scenario], role));
  } catch {
    return NextResponse.json(
      { code: "INVALID_INPUT", message: "Invalid request body" },
      { status: 400 }
    );
  }
}
