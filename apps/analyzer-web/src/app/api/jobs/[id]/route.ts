import { NextResponse } from "next/server";
import { confidentResult } from "@/lib/mock-data";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  if (process.env.DEV_MOCK !== "1") {
    return NextResponse.json(
      { code: "NOT_FOUND", message: "Mock routes disabled" },
      { status: 404 }
    );
  }

  return NextResponse.json({
    job_id: params.id,
    status: "completed",
    result: confidentResult,
  });
}
