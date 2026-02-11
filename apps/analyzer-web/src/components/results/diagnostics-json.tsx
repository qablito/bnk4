"use client";

import type { AnalysisOutput } from "@/types/engine-v1";
import { Collapsible } from "../ui/collapsible";

interface DiagnosticsJSONProps {
  output: AnalysisOutput;
}

export function DiagnosticsJSON({ output }: DiagnosticsJSONProps) {
  if (output.role === "guest") return null;

  return (
    <Collapsible title="Raw JSON" data-testid="diagnostics-json">
      <pre
        data-testid="diagnostics-json-content"
        className="text-xs font-mono bg-surface rounded-lg p-4 overflow-x-auto max-h-96 overflow-y-auto border border-border"
      >
        {JSON.stringify(output, null, 2)}
      </pre>
    </Collapsible>
  );
}
