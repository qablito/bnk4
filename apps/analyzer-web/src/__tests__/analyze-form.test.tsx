import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AnalyzeForm } from "@/components/analyze-form";

vi.mock("@/lib/api-client", () => ({
  fetchSamples: vi.fn().mockResolvedValue({
    samples: [
      { id: "s1", name: "Confident Track", url: "mock://confident" },
      { id: "s2", name: "Mode Withheld Track", url: "mock://mode-withheld" },
    ],
  }),
}));

describe("AnalyzeForm", () => {
  it("supports upload/sample/url modes with required inputs", async () => {
    const onSubmit = vi.fn();
    render(<AnalyzeForm onSubmit={onSubmit} isLoading={false} />);

    expect(screen.getByTestId("input-mode-upload")).toBeInTheDocument();
    expect(screen.getByTestId("input-mode-sample")).toBeInTheDocument();
    expect(screen.getByTestId("input-mode-url")).toBeInTheDocument();

    const submit = screen.getByTestId("analyze-submit");
    expect(submit).toBeDisabled();

    const fileInput = screen.getByTestId("file-input") as HTMLInputElement;
    const file = new File(["x"], "clip.mp3", { type: "audio/mpeg" });
    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(submit).not.toBeDisabled();
    fireEvent.click(submit);
    expect(onSubmit).toHaveBeenCalledWith({ role: "pro", file });

    fireEvent.click(screen.getByTestId("input-mode-sample"));
    const sampleSelect = await screen.findByTestId("sample-select");
    fireEvent.change(sampleSelect, { target: { value: "s2" } });
    fireEvent.click(submit);
    expect(onSubmit).toHaveBeenCalledWith({
      role: "pro",
      input: { kind: "sample_id", sample_id: "s2" },
    });

    fireEvent.click(screen.getByTestId("input-mode-url"));
    const urlInput = screen.getByTestId("url-input");
    fireEvent.change(urlInput, { target: { value: "https://x.test/demo.mp3" } });
    fireEvent.click(submit);
    expect(onSubmit).toHaveBeenCalledWith({
      role: "pro",
      input: { kind: "url", url: "https://x.test/demo.mp3" },
    });

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(3);
    });
  });
});
