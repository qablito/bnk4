"use client";

import { useState } from "react";
import type { AnalyzeRequest, AnalyzeUploadParams } from "@/types/api";
import type { AnalysisOutput } from "@/types/engine-v1";
import { APIError } from "@/types/api";
import { analyzeWithPolling } from "@/lib/api-client";
import { AnalyzeForm } from "@/components/analyze-form";
import { ResultsView } from "@/components/results/results-view";
import { ErrorBoundary } from "@/components/error-boundary";
import { Spinner } from "@/components/ui/spinner";
import { Card } from "@/components/ui/card";

export default function HomePage() {
  const [result, setResult] = useState<AnalysisOutput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(payload: AnalyzeRequest | AnalyzeUploadParams) {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const output = await analyzeWithPolling(payload);
      setResult(output);
    } catch (err) {
      if (err instanceof APIError) {
        setError(`[${err.code}] ${err.message}`);
      } else {
        setError((err as Error).message || "An unexpected error occurred");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <AnalyzeForm onSubmit={handleSubmit} isLoading={isLoading} />

      {isLoading && (
        <div data-testid="loading-state" className="py-12">
          <Spinner />
          <p className="text-center text-sm text-text-secondary mt-3">
            Analyzing audio...
          </p>
        </div>
      )}

      {error && (
        <Card data-testid="error-state" className="text-center py-6">
          <p className="text-red-500 font-semibold mb-1">Analysis failed</p>
          <p className="text-sm text-text-secondary">{error}</p>
        </Card>
      )}

      {result && (
        <ErrorBoundary>
          <ResultsView output={result} />
        </ErrorBoundary>
      )}
    </div>
  );
}
