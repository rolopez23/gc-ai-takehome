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

function makeStreamResponse(events: object[]): Response {
  const body = events.map((e) => JSON.stringify(e) + "\n").join("");
  return new Response(body, {
    status: 200,
    headers: { "content-type": "application/x-ndjson" },
  });
}

/** Creates a stream that sends events then stays open (doesn't close). */
function makeStallingStream(events: object[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const e of events) {
        controller.enqueue(encoder.encode(JSON.stringify(e) + "\n"));
      }
      // Don't close — stream stays alive so the component stays in streaming state
    },
  });
  return new Response(body, {
    status: 200,
    headers: { "content-type": "application/x-ndjson" },
  });
}

const COMPLETED_STREAM = [
  { event: "started", review_id: REVIEW_ID, summary: "", call_to_action: [] },
  { event: "verifying", is_contract: true },
  { event: "splitting", agreement_type: "SaaS MSA", clause_count: 3 },
  {
    event: "clause_evaluated",
    clause: {
      section_number: "1.1",
      clause_type: "Payment Terms",
      severity: 3,
      fairness: "fair",
      finding: "Standard payment terms.",
    },
  },
  {
    event: "clause_evaluated",
    clause: {
      section_number: "4.2",
      clause_type: "Limitation of Liability",
      severity: 8,
      fairness: "non-standard",
      finding: "Liability capped at 3 months.",
    },
  },
  {
    event: "clause_evaluated",
    clause: {
      section_number: "7.1",
      clause_type: "Termination",
      severity: 9,
      fairness: "dealbreaker",
      finding: "Unilateral termination right.",
    },
  },
  { event: "replace", field: "summary", text: "Looks good" },
  { event: "replace", field: "call_to_action", value: [] },
  {
    event: "completed",
    result: {
      overall_fairness: "fair",
      agreement_type: "SaaS MSA",
      summary: "Looks good",
      call_to_action: [],
      clauses: [],
    },
  },
];

const FAILED_STREAM = [
  { event: "started", review_id: REVIEW_ID, summary: "", call_to_action: [] },
  {
    event: "failed",
    reason: "An error occurred during contract evaluation. Please try again.",
  },
];

const REJECTED_STREAM = [
  { event: "started", review_id: REVIEW_ID, summary: "", call_to_action: [] },
  { event: "rejected", reason: "This is a recipe, not a contract." },
];

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

  it("sends FormData POST to backend upload endpoint with stream=true", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStreamResponse(COMPLETED_STREAM));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/contracts/upload?stream=true"),
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

  it("streams until completed then navigates", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStreamResponse(COMPLETED_STREAM));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(
      () => {
        expect(mockPush).toHaveBeenCalledWith(`/contract/${CONTRACT_ID}`);
      },
      { timeout: 5000 },
    );
  });

  it("shows error on failed stream", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStreamResponse(FAILED_STREAM));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "An error occurred during contract evaluation",
      );
    });
  });

  it("shows 'Try again' button on failed stream", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStreamResponse(FAILED_STREAM));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /try again/i }),
      ).toBeInTheDocument();
    });
  });

  it("shows rejection reason on rejected stream", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStreamResponse(REJECTED_STREAM));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("recipe");
    });
  });

  it("shows 'Try another' button on rejected stream", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStreamResponse(REJECTED_STREAM));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /try another/i }),
      ).toBeInTheDocument();
    });
  });

  it("shows error when stream endpoint returns non-200", async () => {
    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response("", { status: 500 }));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Stream unavailable");
    });
  });

  it("shows stage headline 'Uploading document...' during upload", async () => {
    // Never resolve the upload — just check headline appears
    mockFetch.mockReturnValueOnce(new Promise(() => {}));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("stage-headline")).toHaveTextContent(
        "Uploading document...",
      );
    });
  });

  it("shows stage headline 'Verifying document...' on verifying event", async () => {
    const events = [
      {
        event: "started",
        review_id: REVIEW_ID,
        summary: "",
        call_to_action: [],
      },
      { event: "verifying", is_contract: true },
    ];

    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStallingStream(events));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("stage-headline")).toHaveTextContent(
        "Verifying document...",
      );
    });
  });

  it("shows splitting headline with agreement type and count", async () => {
    const events = [
      {
        event: "started",
        review_id: REVIEW_ID,
        summary: "",
        call_to_action: [],
      },
      { event: "splitting", agreement_type: "NDA", clause_count: 8 },
    ];

    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStallingStream(events));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("stage-headline")).toHaveTextContent(
        "Splitting NDA into 8 clauses...",
      );
    });
  });

  it("shows stats bar with correct counts after clause events", async () => {
    const events = [
      {
        event: "started",
        review_id: REVIEW_ID,
        summary: "",
        call_to_action: [],
      },
      { event: "splitting", agreement_type: "NDA", clause_count: 5 },
      {
        event: "clause_evaluated",
        clause: {
          section_number: "1",
          clause_type: "Scope",
          severity: 2,
          fairness: "fair",
          finding: "Fine.",
        },
      },
      {
        event: "clause_evaluated",
        clause: {
          section_number: "2",
          clause_type: "Term",
          severity: 7,
          fairness: "non-standard",
          finding: "Odd.",
        },
      },
      {
        event: "clause_evaluated",
        clause: {
          section_number: "3",
          clause_type: "Liability",
          severity: 10,
          fairness: "dealbreaker",
          finding: "Bad.",
        },
      },
    ];

    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStallingStream(events));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("stat-dealbreaker")).toHaveTextContent("1");
      expect(screen.getByTestId("stat-nonstandard")).toHaveTextContent("1");
      expect(screen.getByTestId("stat-fair")).toHaveTextContent("1");
    });
  });

  it("shows progress bar during evaluating stage", async () => {
    const events = [
      {
        event: "started",
        review_id: REVIEW_ID,
        summary: "",
        call_to_action: [],
      },
      { event: "splitting", agreement_type: "NDA", clause_count: 4 },
      {
        event: "clause_evaluated",
        clause: {
          section_number: "1",
          clause_type: "Scope",
          severity: 2,
          fairness: "fair",
          finding: "Fine.",
        },
      },
    ];

    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStallingStream(events));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      expect(screen.getByTestId("progress-bar")).toBeInTheDocument();
      expect(screen.getByTestId("progress-bar")).toHaveTextContent(
        "Evaluated 1 of 4 clauses",
      );
    });
  });

  it("shows last clause preview during evaluating stage", async () => {
    const events = [
      {
        event: "started",
        review_id: REVIEW_ID,
        summary: "",
        call_to_action: [],
      },
      { event: "splitting", agreement_type: "NDA", clause_count: 2 },
      {
        event: "clause_evaluated",
        clause: {
          section_number: "4.2",
          clause_type: "Limitation of Liability",
          severity: 8,
          fairness: "non-standard",
          finding: "Liability capped at 3 months.",
        },
      },
    ];

    mockFetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
      )
      .mockResolvedValueOnce(makeStallingStream(events));

    render(<EvaluateContractPage />);
    await selectFileAndSubmit();

    await waitFor(() => {
      const preview = screen.getByTestId("clause-preview");
      expect(preview).toHaveTextContent("4.2");
      expect(preview).toHaveTextContent("Limitation of Liability");
      expect(preview).toHaveTextContent("Liability capped at 3 months.");
    });
  });
});
