"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchSamples } from "@/lib/api-client";
import type { AnalyzeRequest, AnalyzeUploadParams } from "@/types/api";
import type { Role } from "@/types/engine-v1";
import { Card } from "./ui/card";

type InputMode = "upload" | "sample" | "url";

type AnalyzePayload = AnalyzeRequest | AnalyzeUploadParams;

interface AnalyzeFormProps {
  onSubmit: (payload: AnalyzePayload) => void | Promise<void>;
  isLoading: boolean;
}

export function AnalyzeForm({ onSubmit, isLoading }: AnalyzeFormProps) {
  const [mode, setMode] = useState<InputMode>("upload");
  const [role, setRole] = useState<Role>("pro");
  const [file, setFile] = useState<File | null>(null);
  const [sampleId, setSampleId] = useState("");
  const [url, setUrl] = useState("");
  const [samples, setSamples] = useState<Array<{ id: string; name: string }>>([]);

  useEffect(() => {
    let active = true;
    void fetchSamples()
      .then((res) => {
        if (!active) return;
        setSamples(res.samples.map((s) => ({ id: s.id, name: s.name })));
      })
      .catch(() => {
        if (!active) return;
        setSamples([]);
      });
    return () => {
      active = false;
    };
  }, []);

  const canSubmit = useMemo(() => {
    if (mode === "upload") return file !== null;
    if (mode === "sample") return sampleId.trim().length > 0;
    return url.trim().length > 0;
  }, [file, mode, sampleId, url]);

  function buildPayload(): AnalyzePayload | null {
    if (mode === "upload") {
      if (!file) return null;
      return { role, file };
    }
    if (mode === "sample") {
      if (!sampleId.trim()) return null;
      return { role, input: { kind: "sample_id", sample_id: sampleId } };
    }
    if (!url.trim()) return null;
    return { role, input: { kind: "url", url: url.trim() } };
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = buildPayload();
    if (!payload) return;
    onSubmit(payload);
  }

  return (
    <Card data-testid="analyze-form">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            data-testid="input-mode-upload"
            onClick={() => setMode("upload")}
            className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
              mode === "upload"
                ? "bg-accent text-white border-accent"
                : "bg-surface text-text-secondary border-border"
            }`}
            disabled={isLoading}
          >
            Upload file
          </button>
          <button
            type="button"
            data-testid="input-mode-sample"
            onClick={() => setMode("sample")}
            className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
              mode === "sample"
                ? "bg-accent text-white border-accent"
                : "bg-surface text-text-secondary border-border"
            }`}
            disabled={isLoading}
          >
            Pick sample
          </button>
          <button
            type="button"
            data-testid="input-mode-url"
            onClick={() => setMode("url")}
            className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
              mode === "url"
                ? "bg-accent text-white border-accent"
                : "bg-surface text-text-secondary border-border"
            }`}
            disabled={isLoading}
          >
            URL
          </button>
        </div>

        {mode === "upload" && (
          <div>
            <label
              htmlFor="file-input"
              className="block text-sm font-medium text-text-secondary mb-1"
            >
              Audio file
            </label>
            <input
              id="file-input"
              data-testid="file-input"
              type="file"
              accept="audio/*"
              onChange={(e) => {
                const selected = e.target.files?.[0] || null;
                setFile(selected);
              }}
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-text-primary file:mr-3 file:px-3 file:py-1 file:rounded-md file:border-0 file:bg-accent file:text-white"
              disabled={isLoading}
            />
          </div>
        )}

        {mode === "sample" && (
          <div>
            <label
              htmlFor="sample-select"
              className="block text-sm font-medium text-text-secondary mb-1"
            >
              Sample
            </label>
            <select
              id="sample-select"
              data-testid="sample-select"
              value={sampleId}
              onChange={(e) => setSampleId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
              disabled={isLoading}
            >
              <option value="">Select a sample</option>
              {samples.map((sample) => (
                <option key={sample.id} value={sample.id}>
                  {sample.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {mode === "url" && (
          <div>
            <label
              htmlFor="url-input"
              className="block text-sm font-medium text-text-secondary mb-1"
            >
              Sample URL
            </label>
            <input
              id="url-input"
              data-testid="url-input"
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/track.mp3"
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:ring-2 focus:ring-accent/50"
              disabled={isLoading}
            />
          </div>
        )}

        <div>
          <label
            htmlFor="role-select"
            className="block text-sm font-medium text-text-secondary mb-1"
          >
            Role
          </label>
          <select
            id="role-select"
            data-testid="role-select"
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
            disabled={isLoading}
          >
            <option value="guest">Guest</option>
            <option value="free">Free</option>
            <option value="pro">Pro</option>
          </select>
        </div>

        <button
          type="submit"
          data-testid="analyze-submit"
          disabled={isLoading || !canSubmit}
          className="w-full px-4 py-2.5 rounded-lg bg-accent text-white font-medium hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? "Analyzing..." : "Analyze"}
        </button>
      </form>
    </Card>
  );
}
