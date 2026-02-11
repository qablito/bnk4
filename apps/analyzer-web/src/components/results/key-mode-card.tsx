import type { KeyModeMetric } from "@/types/engine-v1";
import { confidenceColor, capitalize } from "@/lib/utils";
import { Badge } from "../ui/badge";
import { Card, CardHeader, CardTitle } from "../ui/card";
import { CandidatesTable } from "./candidates-table";
import { Collapsible } from "../ui/collapsible";

interface KeyModeCardProps {
  keyMode: KeyModeMetric;
  isGuest: boolean;
}

export function KeyModeCard({ keyMode, isGuest }: KeyModeCardProps) {
  const hasKey = keyMode.value !== null;
  const hasMode = keyMode.mode !== null;
  const modeWithheld =
    hasKey &&
    !hasMode &&
    keyMode.reason_codes?.includes("mode_withheld_insufficient_evidence");

  return (
    <Card data-testid="key-mode-card">
      <CardHeader>
        <CardTitle>Key / Mode</CardTitle>
        {!isGuest && keyMode.confidence && (
          <Badge
            data-testid="key-confidence"
            className={confidenceColor(keyMode.confidence)}
          >
            {capitalize(keyMode.confidence)}
          </Badge>
        )}
      </CardHeader>

      {hasKey ? (
        <div className="flex items-baseline gap-3">
          <p data-testid="key-value" className="text-4xl font-bold tracking-tight">
            {keyMode.value}
          </p>
          {hasMode ? (
            <p data-testid="key-mode-value" className="text-xl text-text-secondary">
              {capitalize(keyMode.mode!)}
            </p>
          ) : modeWithheld ? (
            <Badge
              data-testid="mode-withheld-badge"
              className="bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
            >
              Mode withheld
            </Badge>
          ) : (
            <p className="text-text-secondary">—</p>
          )}
        </div>
      ) : (
        <p data-testid="key-omitted" className="text-lg text-text-secondary italic">
          Omitted (low confidence)
        </p>
      )}

      {!isGuest && keyMode.reason_codes && keyMode.reason_codes.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {keyMode.reason_codes.map((code) => (
            <Badge
              key={code}
              data-testid="key-reason-code"
              className="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
            >
              {code}
            </Badge>
          ))}
        </div>
      )}

      {!isGuest && keyMode.candidates && keyMode.candidates.length > 0 && (
        <div className="mt-4">
          <Collapsible title="Candidates" data-testid="key-candidates">
            <CandidatesTable
              columns={["Rank", "Key", "Mode", "Score", "Family"]}
              rows={keyMode.candidates.map((c) => [
                String(c.rank),
                c.key,
                c.mode || "—",
                c.score.toFixed(4),
                c.family,
              ])}
              data-testid="key-candidates-table"
            />
          </Collapsible>
        </div>
      )}
    </Card>
  );
}
