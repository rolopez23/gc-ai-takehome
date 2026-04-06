import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import EvaluateContractPage from "@/app/evaluate-contract/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Cancel on unmount", () => {
  test("cancels in-flight request when component unmounts", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => {})),
    );

    const { unmount } = render(<EvaluateContractPage />);

    const file = new File(["contract"], "contract.txt", { type: "text/plain" });
    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file,
    );
    await userEvent.click(
      screen.getByRole("button", { name: /evaluate contract/i }),
    );

    // Streaming view should be visible (uploading stage)
    expect(screen.getByTestId("streaming-view")).toBeInTheDocument();

    unmount();

    const fetchCall = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const signal = fetchCall[1]?.signal as AbortSignal;
    expect(signal).toBeDefined();
    expect(signal.aborted).toBe(true);
  });

  test("does not show error message on abort", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(
              new DOMException("The operation was aborted.", "AbortError"),
            );
          });
        });
      }),
    );

    const { unmount } = render(<EvaluateContractPage />);

    const file = new File(["contract"], "contract.txt", { type: "text/plain" });
    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file,
    );
    await userEvent.click(
      screen.getByRole("button", { name: /evaluate contract/i }),
    );

    unmount();

    expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument();
  });
});
