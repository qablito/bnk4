import type { AnalysisOutput } from "@/types/engine-v1";
import { BPMCard } from "./bpm-card";
import { KeyModeCard } from "./key-mode-card";
import { TransparencyPanel } from "./transparency-panel";
import { DiagnosticsJSON } from "./diagnostics-json";

interface ResultsViewProps {
  output: AnalysisOutput;
}

export function ResultsView({ output }: ResultsViewProps) {
  const isGuest = output.role === "guest";

  return (
    <div data-testid="results-view" className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        {output.metrics.bpm && (
          <BPMCard bpm={output.metrics.bpm} isGuest={isGuest} />
        )}
        {output.metrics.key && (
          <KeyModeCard keyMode={output.metrics.key} isGuest={isGuest} />
        )}
      </div>

      <TransparencyPanel output={output} />
      <DiagnosticsJSON output={output} />
    </div>
  );
}
