import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import ClauseCard from "@/app/contract/[id]/ClauseCard";
import ClauseSection from "@/app/contract/[id]/ClauseSection";
import type { ReviewClause } from "@/app/evaluate-contract/types";

const TEST_CLAUSE: ReviewClause = {
  section_number: "3.1",
  clause_type: "Liability Cap",
  purpose: "Limits financial exposure",
  fairness: "dealbreaker",
  market_standard: "Typically 12 months of fees",
  explanation: "Unlimited liability is unacceptable",
  severity: 9,
};

const TEST_CLAUSE_NO_SEVERITY: ReviewClause = {
  section_number: "4.1",
  clause_type: "Governing Law",
  purpose: "Sets jurisdiction",
  fairness: "fair",
  market_standard: "Standard",
  explanation: "Standard governing law clause",
};

const TEST_CLAUSE_2: ReviewClause = {
  section_number: "5.2",
  clause_type: "Payment Terms",
  purpose: "Defines payment schedule",
  fairness: "dealbreaker",
  market_standard: "Net 30",
  explanation: "Net 15 is aggressive but negotiable",
  severity: 6,
};

describe("ClauseCard", () => {
  it("renders section_number, clause_type, and explanation", () => {
    render(<ClauseCard clause={TEST_CLAUSE} fairness="dealbreaker" />);
    expect(screen.getByText("3.1")).toBeInTheDocument();
    expect(screen.getByText("Liability Cap")).toBeInTheDocument();
    expect(
      screen.getByText("Unlimited liability is unacceptable"),
    ).toBeInTheDocument();
  });

  it("applies fairness-colored left border", () => {
    const { container } = render(
      <ClauseCard clause={TEST_CLAUSE} fairness="dealbreaker" />,
    );
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain("border-l-2");
    expect(card.className).toContain("border-l-egregious-border");
  });
});

describe("ClauseSection", () => {
  it("renders header with label and count", () => {
    render(
      <ClauseSection
        rating="dealbreaker"
        clauses={[TEST_CLAUSE, TEST_CLAUSE_2]}
      />,
    );
    expect(screen.getByText(/Dealbreaker/)).toBeInTheDocument();
    expect(screen.getByText(/\(2\)/)).toBeInTheDocument();
  });

  it("starts collapsed — clauses not visible", () => {
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE]} />);
    expect(
      screen.queryByText("Unlimited liability is unacceptable"),
    ).not.toBeInTheDocument();
  });

  it("clicking header expands section and shows clauses", async () => {
    const user = userEvent.setup();
    render(
      <ClauseSection
        rating="dealbreaker"
        clauses={[TEST_CLAUSE, TEST_CLAUSE_2]}
      />,
    );
    await user.click(screen.getByRole("button"));
    expect(
      screen.getByText("Unlimited liability is unacceptable"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Net 15 is aggressive but negotiable"),
    ).toBeInTheDocument();
  });

  it("clicking header again collapses section", async () => {
    const user = userEvent.setup();
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE]} />);
    await user.click(screen.getByRole("button"));
    expect(
      screen.getByText("Unlimited liability is unacceptable"),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button"));
    expect(
      screen.queryByText("Unlimited liability is unacceptable"),
    ).not.toBeInTheDocument();
  });

  it("renders celebratory placeholder for empty dealbreaker section", () => {
    render(<ClauseSection rating="dealbreaker" clauses={[]} />);
    expect(screen.getByText(/No dealbreaker clauses/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders celebratory placeholder for empty non-standard section", () => {
    render(<ClauseSection rating="non-standard" clauses={[]} />);
    expect(screen.getByText(/No non-standard clauses/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders warning placeholder for empty fair section", () => {
    render(<ClauseSection rating="fair" clauses={[]} />);
    expect(screen.getByText(/No standard clauses found/)).toBeInTheDocument();
    expect(screen.getByText("⚠")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("expanded section renders clause list", async () => {
    const user = userEvent.setup();
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE]} />);
    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("list")).toBeInTheDocument();
  });
});

describe("ClauseCard severity display", () => {
  it("shows severity score when clause has severity", () => {
    render(<ClauseCard clause={TEST_CLAUSE} fairness="dealbreaker" />);
    expect(screen.getByText("Severity: 9/10")).toBeInTheDocument();
  });

  it("does not show severity when clause has no severity", () => {
    render(<ClauseCard clause={TEST_CLAUSE_NO_SEVERITY} fairness="fair" />);
    expect(screen.queryByText(/Severity:/)).not.toBeInTheDocument();
  });
});
