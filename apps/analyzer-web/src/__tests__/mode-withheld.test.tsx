import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultsView } from "@/components/results/results-view";
import { modeWithheldResult, confidentResult } from "@/lib/mock-data";

describe("Mode withheld", () => {
  it('renders "Mode withheld" badge when key present and mode is null with reason code', () => {
    render(<ResultsView output={modeWithheldResult} />);

    expect(screen.getByTestId("key-value")).toHaveTextContent("A");
    expect(screen.getByTestId("mode-withheld-badge")).toHaveTextContent(
      "Mode withheld"
    );
    expect(screen.queryByTestId("key-mode-value")).not.toBeInTheDocument();
  });

  it("shows reason codes including mode_withheld_insufficient_evidence", () => {
    render(<ResultsView output={modeWithheldResult} />);

    const codes = screen.getAllByTestId("key-reason-code");
    const texts = codes.map((el) => el.textContent);
    expect(texts).toContain("mode_withheld_insufficient_evidence");
  });

  it("does NOT show mode-withheld badge when mode is present", () => {
    render(<ResultsView output={confidentResult} />);

    expect(screen.queryByTestId("mode-withheld-badge")).not.toBeInTheDocument();
    expect(screen.getByTestId("key-mode-value")).toHaveTextContent("Minor");
  });

  it("shows candidates as key_aggregate family when mode is withheld", () => {
    render(<ResultsView output={modeWithheldResult} />);

    // The candidates should have mode "—" (null) and family "key_aggregate"
    const keyMode = modeWithheldResult.metrics.key!;
    expect(keyMode.candidates![0].family).toBe("key_aggregate");
    expect(keyMode.candidates![0].mode).toBeNull();
  });
});
