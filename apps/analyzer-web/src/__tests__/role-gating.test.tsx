import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultsView } from "@/components/results/results-view";
import { confidentResult, guestResult } from "@/lib/mock-data";
import type { AnalysisOutput } from "@/types/engine-v1";

describe("Role gating", () => {
  describe("Guest role", () => {
    it("hides confidence badges for guest", () => {
      render(<ResultsView output={guestResult} />);

      expect(screen.queryByTestId("bpm-confidence")).not.toBeInTheDocument();
      expect(screen.queryByTestId("key-confidence")).not.toBeInTheDocument();
    });

    it("hides candidates for guest", () => {
      render(<ResultsView output={guestResult} />);

      expect(screen.queryByTestId("bpm-candidates")).not.toBeInTheDocument();
      expect(screen.queryByTestId("key-candidates")).not.toBeInTheDocument();
    });

    it("hides transparency panel for guest", () => {
      render(<ResultsView output={guestResult} />);

      expect(screen.queryByTestId("transparency-panel")).not.toBeInTheDocument();
    });

    it("hides diagnostics JSON for guest", () => {
      render(<ResultsView output={guestResult} />);

      expect(screen.queryByTestId("diagnostics-json")).not.toBeInTheDocument();
    });

    it("still shows BPM value for guest", () => {
      render(<ResultsView output={guestResult} />);

      expect(screen.getByTestId("bpm-value")).toHaveTextContent("128");
    });
  });

  describe("Free/Pro role", () => {
    it("shows confidence badges for pro", () => {
      render(<ResultsView output={confidentResult} />);

      expect(screen.getByTestId("bpm-confidence")).toBeInTheDocument();
      expect(screen.getByTestId("key-confidence")).toBeInTheDocument();
    });

    it("shows transparency panel for pro", () => {
      render(<ResultsView output={confidentResult} />);

      expect(screen.getByTestId("transparency-panel")).toBeInTheDocument();
    });

    it("shows candidates collapsible for pro", () => {
      render(<ResultsView output={confidentResult} />);

      expect(screen.getByTestId("bpm-candidates")).toBeInTheDocument();
      expect(screen.getByTestId("key-candidates")).toBeInTheDocument();
    });

    it("shows reason codes for pro", () => {
      render(<ResultsView output={confidentResult} />);

      const reasonCodes = screen.getAllByTestId("key-reason-code");
      expect(reasonCodes.length).toBeGreaterThan(0);
      expect(reasonCodes[0]).toHaveTextContent("emit_confident");
    });

    it("works for free role identically to pro", () => {
      const freeResult: AnalysisOutput = { ...confidentResult, role: "free" };
      render(<ResultsView output={freeResult} />);

      expect(screen.getByTestId("bpm-confidence")).toBeInTheDocument();
      expect(screen.getByTestId("transparency-panel")).toBeInTheDocument();
    });
  });
});
