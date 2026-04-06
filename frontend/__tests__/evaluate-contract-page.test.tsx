import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import EvaluateContractPage from "@/app/evaluate-contract/page";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const CONTRACT_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d";
const REVIEW_ID = "f6e5d4c3-b2a1-4f9e-8d7c-6b5a4c3d2e1f";

const UPLOAD_RESPONSE = {
  contract_id: CONTRACT_ID,
  review_id: REVIEW_ID,
  status: "pending",
};

const REVIEW_EVALUATING = {
  id: REVIEW_ID,
  contract_id: CONTRACT_ID,
  status: "evaluating",
};

const REVIEW_COMPLETED = {
  id: REVIEW_ID,
  contract_id: CONTRACT_ID,
  status: "completed",
  overall_fairness: "fair",
  summary: "Looks good",
  call_to_action: [],
  clauses: [],
  completed_at: "2026-01-01T00:00:00Z",
};

const REVIEW_FAILED = {
  id: REVIEW_ID,
  status: "failed",
  failure_message: "LLM unavailable",
  failure_code: null,
};

let mockFetch: ReturnType<typeof vi.fn>;

beforeEach(() => {
  mockFetch = vi.fn();
  vi.stubGlobal("fetch", mockFetch);
  mockPush.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

async function selectFileAndSubmit() {
  const file = new File(["content"], "contract.txt", { type: "text/plain" });
  await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
  await userEvent.click(screen.getByRole("button", { name: /evaluate/i }));
}

describe("EvaluateContractPage", () => {
  it("renders the page heading", () => {
    render(<EvaluateContractPage />);
    expect(
      screen.getByRole("heading", { name: /evaluate/i }),
    ).toBeInTheDocument();
  });

  it("disables submit button when no file is staged", () => {
    render(<EvaluateContractPage />);
    expect(screen.getByRole("button", { name: /evaluate/i })).toBeDisabled();
  });

  it("sends FormData POST to backend upload endpoint", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(REVIEW_COMPLETED), { status: 200 }),
      );

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/contracts/upload"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.body).toBeInstanceOf(FormData);
    expect(opts.body.get("file")).toBeInstanceOf(File);
  });

  it("shows error on upload 400", async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Unsupported file type" }), {
        status: 400,
      }),
    );

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Unsupported file type",
      );
    });
  });

  it("polls until completed then navigates", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(REVIEW_EVALUATING), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(REVIEW_COMPLETED), { status: 200 }),
      );

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(
      () => {
        expect(mockPush).toHaveBeenCalledWith(`/contract/${CONTRACT_ID}`);
      },
      { timeout: 5000 },
    );
  });

  it("shows failure message on failed review", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(REVIEW_FAILED), { status: 200 }),
      );

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Something went wrong",
      );
    });
  });

  it("shows status text during polling", async () => {
    let resolveSecondPoll: (v: Response) => void;
    const secondPollPromise = new Promise<Response>((r) => {
      resolveSecondPoll = r;
    });

    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(REVIEW_EVALUATING), { status: 200 }),
      )
      .mockImplementationOnce(() => secondPollPromise);

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("status-text")).toHaveTextContent(
        "Evaluating contract...",
      );
    });

    // Clean up: resolve the pending poll so the component unmounts cleanly
    resolveSecondPoll!(
      new Response(JSON.stringify(REVIEW_COMPLETED), { status: 200 }),
    );
  });

  it("does not clear instructions when file is removed", async () => {
    render(<EvaluateContractPage />);

    await userEvent.type(
      screen.getByPlaceholderText(/instruction/i),
      "Check indemnification",
    );

    const file = new File(["content"], "contract.txt", { type: "text/plain" });
    await userEvent.upload(
      screen.getByLabelText(/upload contract file/i),
      file,
    );
    await userEvent.click(screen.getByRole("button", { name: /remove/i }));

    expect(screen.getByPlaceholderText(/instruction/i)).toHaveValue(
      "Check indemnification",
    );
  });
});
