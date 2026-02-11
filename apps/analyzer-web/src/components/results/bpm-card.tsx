import type { BPMMetric } from "@/types/engine-v1";
import { confidenceColor, capitalize } from "@/lib/utils";
import { Badge } from "../ui/badge";
import { Card, CardHeader, CardTitle } from "../ui/card";
import { CandidatesTable } from "./candidates-table";
import { Collapsible } from "../ui/collapsible";

interface BPMCardProps {
  bpm: BPMMetric;
  isGuest: boolean;
}

export function BPMCard({ bpm, isGuest }: BPMCardProps) {
  const hasValue = bpm.value !== undefined;

  return (
    <Card data-testid="bpm-card">
      <CardHeader>
        <CardTitle>BPM</CardTitle>
        {!isGuest && bpm.confidence && (
          <Badge
            data-testid="bpm-confidence"
            className={confidenceColor(bpm.confidence)}
          >
            {capitalize(bpm.confidence)}
          </Badge>
        )}
      </CardHeader>

      {hasValue ? (
        <div className="space-y-1">
          <p data-testid="bpm-value" className="text-4xl font-bold tracking-tight">
            {bpm.value!.value_rounded}
          </p>
          {!isGuest && bpm.value!.value_exact !== undefined && (
            <p className="text-sm text-text-secondary">
              Exact: {bpm.value!.value_exact.toFixed(1)}
            </p>
          )}
        </div>
      ) : (
        <p data-testid="bpm-omitted" className="text-lg text-text-secondary italic">
          Omitted (low confidence)
        </p>
      )}

      {!isGuest && bpm.bpm_reportable !== undefined && (
        <div className="mt-3 text-sm text-text-secondary space-y-0.5">
          {bpm.bpm_raw != null && <p>Raw: {bpm.bpm_raw}</p>}
          {bpm.bpm_reportable != null && <p>Reportable: {bpm.bpm_reportable}</p>}
          {bpm.timefeel && <p>Timefeel: {bpm.timefeel}</p>}
        </div>
      )}

      {!isGuest && bpm.candidates && bpm.candidates.length > 0 && (
        <div className="mt-4">
          <Collapsible title="Candidates" data-testid="bpm-candidates">
            <CandidatesTable
              columns={["Rank", "BPM", "Score", "Relation"]}
              rows={bpm.candidates.map((c) => [
                String(c.rank),
                String(c.value.value_rounded),
                c.score.toFixed(4),
                c.relation,
              ])}
              data-testid="bpm-candidates-table"
            />
          </Collapsible>
        </div>
      )}

      {!isGuest && bpm.bpm_reason_codes && bpm.bpm_reason_codes.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {bpm.bpm_reason_codes.map((code) => (
            <Badge
              key={code}
              data-testid="bpm-reason-code"
              className="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
            >
              {code}
            </Badge>
          ))}
        </div>
      )}
    </Card>
  );
}
