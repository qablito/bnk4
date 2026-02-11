import type { AnalysisOutput } from "@/types/engine-v1";
import { Card, CardHeader, CardTitle } from "../ui/card";
import { Collapsible } from "../ui/collapsible";

interface TransparencyPanelProps {
  output: AnalysisOutput;
}

export function TransparencyPanel({ output }: TransparencyPanelProps) {
  if (output.role === "guest") return null;

  return (
    <Card data-testid="transparency-panel">
      <CardHeader>
        <CardTitle>Transparency</CardTitle>
      </CardHeader>

      <div className="space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <span className="text-text-secondary">Engine</span>
          <span>{output.engine.name} {output.engine.version}</span>
          <span className="text-text-secondary">Analysis ID</span>
          <span className="font-mono text-xs break-all">{output.analysis_id}</span>
          <span className="text-text-secondary">Role</span>
          <span>{output.role}</span>
          <span className="text-text-secondary">Created</span>
          <span>{output.created_at}</span>
        </div>

        {output.track && (
          <Collapsible title="Track Info" data-testid="track-info">
            <div className="grid grid-cols-2 gap-1 text-sm">
              <span className="text-text-secondary">Duration</span>
              <span>{output.track.duration_seconds.toFixed(1)}s</span>
              <span className="text-text-secondary">Sample Rate</span>
              <span>{output.track.sample_rate_hz} Hz</span>
              <span className="text-text-secondary">Channels</span>
              <span>{output.track.channels}</span>
              <span className="text-text-secondary">Format</span>
              <span>{output.track.format}</span>
            </div>
          </Collapsible>
        )}

        {output.warnings && output.warnings.length > 0 && (
          <Collapsible title={`Warnings (${output.warnings.length})`} data-testid="warnings">
            <ul className="list-disc pl-4 text-amber-600 dark:text-amber-400">
              {output.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </Collapsible>
        )}
      </div>
    </Card>
  );
}
