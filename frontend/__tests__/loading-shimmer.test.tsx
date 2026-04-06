import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import EvaluateContractPage from "@/app/evaluate-contract/page";
import { LoadingShimmer } from "@/app/evaluate-contract/LoadingShimmer";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const UPLOAD_RESPONSE = {
  contract_id: "452be08b-a29d-402f-8f44-6b1a0f976efa",
  review_id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
  status: "pending",
};

const REVIEW_ID = "a9198839-1da3-4fb3-ac30-c462cc81ee4e";

function makeStreamResponse(events: object[]): Response {
  const body = events.map((e) => JSON.stringify(e) + "\n").join("");
  return new Response(body, {
    status: 200,
    headers: { "content-type": "application/x-ndjson" },
  });
}

function makeStallingStream(events: object[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const e of events) {
        controller.enqueue(encoder.encode(JSON.stringify(e) + "\n"));
      }
    },
  });
  return new Response(body, {
    status: 200,
    headers: { "content-type": "application/x-ndjson" },
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

async function stageFileAndSubmit() {
  render(<EvaluateContractPage />);
  const file = new File(["contract text"], "contract.txt", {
    type: "text/plain",
  });
  await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
  await userEvent.click(
    screen.getByRole("button", { name: /evaluate contract/i }),
  );
}

describe("Loading / streaming view", () => {
  test("shows streaming view when submitting", async () => {
    // Upload resolves, stream stays open
    const mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(
        makeStallingStream([
          {
            event: "started",
            review_id: REVIEW_ID,
            summary: "",
            call_to_action: [],
          },
          { event: "verifying", is_contract: true },
        ]),
      );

    await stageFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("streaming-view")).toBeInTheDocument();
    });
  });

  test("hides submit button when streaming", async () => {
    const mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    // Never resolve — stays in uploading state
    mockFetch.mockReturnValueOnce(new Promise(() => {}));

    await stageFileAndSubmit();

    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /evaluate contract/i }),
      ).not.toBeInTheDocument();
    });
  });

  test("sends FormData to backend upload endpoint", async () => {
    const mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    mockFetch.mockReturnValueOnce(new Promise(() => {}));

    await stageFileAndSubmit();

    await waitFor(() => {
      expect(mockFetch.mock.calls[0][0]).toContain("/api/contracts/upload");
      expect(mockFetch.mock.calls[0][1].method).toBe("POST");
      expect(mockFetch.mock.calls[0][1].body).toBeInstanceOf(FormData);
    });
  });

  test("shimmer cards have staggered delay", () => {
    render(<LoadingShimmer statusText="Evaluating..." />);
    const cards = screen.getAllByTestId("shimmer-card");
    expect(cards).toHaveLength(3);
    expect(cards[0].style.animationDelay).toBe("0ms");
    expect(cards[1].style.animationDelay).toBe("150ms");
    expect(cards[2].style.animationDelay).toBe("300ms");
  });

  test("shimmer has fade-in", () => {
    render(<LoadingShimmer statusText="Evaluating..." />);
    const shimmer = screen.getByTestId("loading-shimmer");
    const fadeWrapper = shimmer.firstChild as HTMLElement;
    expect(fadeWrapper.className).toContain(
      "animate-[fadeIn_300ms_ease-out_forwards]",
    );
  });

  test("hides streaming view on failed stream", async () => {
    const mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(
        makeStreamResponse([
          {
            event: "started",
            review_id: REVIEW_ID,
            summary: "",
            call_to_action: [],
          },
          { event: "failed", reason: "Something broke" },
        ]),
      );

    await stageFileAndSubmit();

    await waitFor(() => {
      expect(screen.queryByTestId("streaming-view")).not.toBeInTheDocument();
    });
  });
});
