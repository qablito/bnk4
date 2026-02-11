import { NextResponse } from "next/server";
import { mockSamples } from "@/lib/mock-data";

export async function GET() {
  if (process.env.DEV_MOCK !== "1") {
    return NextResponse.json(
      { code: "NOT_FOUND", message: "Mock routes disabled" },
      { status: 404 }
    );
  }

  return NextResponse.json({ samples: mockSamples });
}
