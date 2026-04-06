import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import type {
  ReviewCompleted,
  ReviewFailed,
  ReviewPolling,
} from "@/app/evaluate-contract/types";

const mockFetch = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "test-contract-id" }),
}));

const COMPLETED_RESULT: ReviewCompleted = {
  id: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  contract_id: "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
  status: "completed",
  overall_fairness: "dealbreaker",
  summary: "1 dealbreaker, 2 negotiating points",
  call_to_action: ["Fix the liability cap"],
  clauses: [
    {
      id: "c3d4e5f6-a7b8-4c9d-ae1f-2a3b4c5d6e7f",
      section_number: "3.1",
      clause_type: "Liability Cap",
      purpose: "Limits financial exposure",
      fairness: "dealbreaker",
      market_standard: "Typically 12 months of fees",
      explanation: "Unlimited liability is unacceptable",
      severity: 9,
    },
    {
      id: "d4e5f6a7-b8c9-4d0e-9f2a-3b4c5d6e7f80",
      section_number: "5.2",
      clause_type: "Payment Terms",
      purpose: "Defines payment schedule",
      fairness: "non-standard",
      market_standard: "Net 30",
      explanation: "Net 15 is aggressive but negotiable",
      severity: 5,
    },
  ],
  completed_at: "2026-01-01T00:00:00Z",
};

const FAILED_RESULT: ReviewFailed = {
  id: "e5f6a7b8-c9d0-4e1f-aa3b-4c5d6e7f8091",
  status: "failed",
  failure_message: "Document could not be processed",
  failure_code: null,
};

const PENDING_RESULT: ReviewPolling = {
  id: "f6a7b8c9-d0e1-4f2a-ab4c-5d6e7f809102",
  contract_id: "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
  status: "pending",
};

function mockFetchResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  });
}

describe("ContractPage", () => {
  beforeEach(() => {
    vi.resetModules();
    mockFetch.mockReset();
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches from backend with correct URL", async () => {
    mockFetch.mockReturnValue(mockFetchResponse(COMPLETED_RESULT));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/contracts/test-contract-id/review"),
        expect.any(Object),
      );
    });
  });

  it("shows clauses when completed", async () => {
    mockFetch.mockReturnValue(mockFetchResponse(COMPLETED_RESULT));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Evaluation complete")).toBeInTheDocument();
    });
    const buttons = screen.getAllByRole("button");
    expect(buttons[0]).toHaveTextContent(/Dealbreaker/);
    expect(buttons[0]).toHaveTextContent("(1)");
    expect(buttons[1]).toHaveTextContent(/Non-Standard/);
    expect(buttons[1]).toHaveTextContent("(1)");
  });

  it("shows score badge when completed with overall_fairness", async () => {
    mockFetch.mockReturnValue(mockFetchResponse(COMPLETED_RESULT));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Dealbreaker")).toBeInTheDocument();
    });
  });

  it("shows not-a-contract message when completed with null fairness", async () => {
    const notContractResult: ReviewCompleted = {
      ...COMPLETED_RESULT,
      overall_fairness: null,
      summary: "This is a recipe, not a contract.",
      clauses: [],
    };
    mockFetch.mockReturnValue(mockFetchResponse(notContractResult));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Not a contract")).toBeInTheDocument();
    });
    expect(
      screen.getByText("This is a recipe, not a contract."),
    ).toBeInTheDocument();
  });

  it("shows friendly error when evaluation failed with known failure_code", async () => {
    const failedWithCode: ReviewFailed = {
      ...FAILED_RESULT,
      failure_code: "anthropic_error",
    };
    mockFetch.mockReturnValue(mockFetchResponse(failedWithCode));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Evaluation failed")).toBeInTheDocument();
    });
    expect(
      screen.getByText(/couldn't reach our AI service/),
    ).toBeInTheDocument();
  });

  it("shows generic error when evaluation failed with null failure_code", async () => {
    mockFetch.mockReturnValue(mockFetchResponse(FAILED_RESULT));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Evaluation failed")).toBeInTheDocument();
    });
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("shows not-found message on 404", async () => {
    mockFetch.mockReturnValue(mockFetchResponse({}, 404));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("No evaluation found")).toBeInTheDocument();
    });
  });

  it("shows loading shimmer while pending", async () => {
    // Never resolve the fetch so we stay in loading state
    mockFetch.mockReturnValue(new Promise(() => {}));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    expect(screen.getByTestId("loading-shimmer")).toBeInTheDocument();
  });

  it("renders sections in severity order: dealbreaker, non-standard, fair", async () => {
    const resultWithAllTiers: ReviewCompleted = {
      ...COMPLETED_RESULT,
      clauses: [
        {
          id: "c3d4e5f6-a7b8-4c9d-ae1f-2a3b4c5d6e7f",
          section_number: "1.1",
          clause_type: "Standard Clause",
          purpose: "Standard",
          fairness: "fair",
          market_standard: "Standard",
          explanation: "This is fair",
        },
        {
          id: "d4e5f6a7-b8c9-4d0e-9f2a-3b4c5d6e7f80",
          section_number: "2.1",
          clause_type: "Risky Clause",
          purpose: "Non-standard",
          fairness: "non-standard",
          market_standard: "Standard",
          explanation: "This is non-standard",
        },
        {
          id: "e5f6a7b8-c9d0-4e1f-aa3b-4c5d6e7f8091",
          section_number: "3.1",
          clause_type: "Dangerous Clause",
          purpose: "Dealbreaker",
          fairness: "dealbreaker",
          market_standard: "Standard",
          explanation: "This is a dealbreaker",
        },
      ],
    };
    mockFetch.mockReturnValue(mockFetchResponse(resultWithAllTiers));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Evaluation complete")).toBeInTheDocument();
    });
    const sections = screen.getAllByRole("button");
    expect(sections[0]).toHaveTextContent(/Dealbreaker/);
    expect(sections[1]).toHaveTextContent(/Non-Standard/);
    expect(sections[2]).toHaveTextContent(/Standard/);
  });

  it("sorts clauses within a bucket by severity (highest first)", async () => {
    const resultWithSeverities: ReviewCompleted = {
      ...COMPLETED_RESULT,
      clauses: [
        {
          id: "c3d4e5f6-a7b8-4c9d-ae1f-2a3b4c5d6e7f",
          section_number: "3.1",
          clause_type: "Low Severity",
          purpose: "Limits exposure",
          fairness: "dealbreaker",
          market_standard: "Standard",
          explanation: "Low severity dealbreaker",
          severity: 3,
        },
        {
          id: "d4e5f6a7-b8c9-4d0e-9f2a-3b4c5d6e7f80",
          section_number: "3.2",
          clause_type: "High Severity",
          purpose: "Critical issue",
          fairness: "dealbreaker",
          market_standard: "Standard",
          explanation: "High severity dealbreaker",
          severity: 9,
        },
      ],
    };
    mockFetch.mockReturnValue(mockFetchResponse(resultWithSeverities));
    const { default: ContractPage } = await import("@/app/contract/[id]/page");
    render(<ContractPage />);
    await waitFor(() => {
      expect(screen.getByText("Evaluation complete")).toBeInTheDocument();
    });
    // Expand the dealbreaker section (first button is the dealbreaker section header)
    const user = (await import("@testing-library/user-event")).default;
    const buttons = screen.getAllByRole("button");
    const dealBreakerButton = buttons.find((b) =>
      b.textContent?.includes("Dealbreaker"),
    )!;
    await user.setup().click(dealBreakerButton);
    // Get clause cards within the expanded section
    const section = screen.getByLabelText("Dealbreaker clauses");
    const items = section.querySelectorAll("li");
    expect(items[0]).toHaveTextContent("High Severity");
    expect(items[1]).toHaveTextContent("Low Severity");
  });
});
