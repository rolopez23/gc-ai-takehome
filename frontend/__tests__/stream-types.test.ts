import { describe, test, expect } from "vitest";
import {
  StartedEventSchema,
  TokenEventSchema,
  VerifyingEventSchema,
  SplittingEventSchema,
  ClauseEvaluatedEventSchema,
  ClauseErrorEventSchema,
  ReplaceEventSchema,
  CompletedEventSchema,
  RejectedEventSchema,
  FailedEventSchema,
  StreamingEventSchema,
  StreamClauseSchema,
} from "@/app/evaluate-contract/stream-types";

describe("StartedEventSchema", () => {
  test("parses valid started event", () => {
    const data = {
      event: "started",
      review_id: "abc-123",
      summary: "Reviewing contract...",
      call_to_action: ["Check section 2"],
    };
    expect(StartedEventSchema.safeParse(data).success).toBe(true);
  });

  test("rejects wrong event type", () => {
    const data = {
      event: "token",
      review_id: "abc-123",
      summary: "x",
      call_to_action: [],
    };
    expect(StartedEventSchema.safeParse(data).success).toBe(false);
  });
});

describe("TokenEventSchema", () => {
  test("parses valid token event", () => {
    const data = { event: "token", field: "summary", text: "This contract " };
    expect(TokenEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("VerifyingEventSchema", () => {
  test("parses valid verifying event", () => {
    const data = { event: "verifying", is_contract: true };
    expect(VerifyingEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("SplittingEventSchema", () => {
  test("parses valid splitting event", () => {
    const data = {
      event: "splitting",
      agreement_type: "NDA",
      clause_count: 5,
    };
    expect(SplittingEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("StreamClauseSchema", () => {
  test("parses minimal clause", () => {
    const data = {
      section_number: "1.1",
      clause_type: "Termination",
      severity: 3,
      fairness: "fair",
    };
    expect(StreamClauseSchema.safeParse(data).success).toBe(true);
  });

  test("parses full clause with all optional fields", () => {
    const data = {
      section_number: "2.1",
      clause_type: "Indemnification",
      severity: 7,
      fairness: "dealbreaker",
      purpose: "Defines indemnification obligations",
      market_standard: "Mutual indemnification is standard",
      explanation: "One-sided indemnification",
      playbook_status: "flagged",
      playbook_position: "Negotiate mutual terms",
      contract_language: "Party A shall indemnify...",
      finding: "Non-mutual indemnification",
      recommended_redline: "Add mutual indemnification",
      status: "evaluated",
      is_synthetic: false,
    };
    expect(StreamClauseSchema.safeParse(data).success).toBe(true);
  });

  test("accepts null for nullable optional fields", () => {
    const data = {
      section_number: "1.1",
      clause_type: "Termination",
      severity: 3,
      fairness: "non-standard",
      playbook_status: null,
      playbook_position: null,
      contract_language: null,
      recommended_redline: null,
    };
    expect(StreamClauseSchema.safeParse(data).success).toBe(true);
  });
});

describe("ClauseEvaluatedEventSchema", () => {
  test("parses valid clause_evaluated event", () => {
    const data = {
      event: "clause_evaluated",
      clause: {
        section_number: "1.1",
        clause_type: "Termination",
        severity: 3,
        fairness: "fair",
      },
    };
    expect(ClauseEvaluatedEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("ClauseErrorEventSchema", () => {
  test("parses valid clause_error event", () => {
    const data = {
      event: "clause_error",
      section_number: "3.2",
      clause_type: "Liability",
      error: "Failed to evaluate clause",
    };
    expect(ClauseErrorEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("ReplaceEventSchema", () => {
  test("parses replace event with text", () => {
    const data = {
      event: "replace",
      field: "summary",
      text: "Updated summary text",
    };
    expect(ReplaceEventSchema.safeParse(data).success).toBe(true);
  });

  test("parses replace event with value array", () => {
    const data = {
      event: "replace",
      field: "call_to_action",
      value: ["Action 1", "Action 2"],
    };
    expect(ReplaceEventSchema.safeParse(data).success).toBe(true);
  });

  test("parses replace event with only field", () => {
    const data = { event: "replace", field: "summary" };
    expect(ReplaceEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("CompletedEventSchema", () => {
  test("parses valid completed event", () => {
    const data = {
      event: "completed",
      result: {
        overall_fairness: "non-standard",
        agreement_type: "NDA",
        summary: "Issues found in indemnification.",
        call_to_action: ["Review section 3"],
        clauses: [
          {
            section_number: "1.1",
            clause_type: "Termination",
            severity: 3,
            fairness: "fair",
          },
        ],
      },
    };
    expect(CompletedEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("RejectedEventSchema", () => {
  test("parses valid rejected event", () => {
    const data = { event: "rejected", reason: "Not a contract" };
    expect(RejectedEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("FailedEventSchema", () => {
  test("parses valid failed event", () => {
    const data = { event: "failed", reason: "Internal error" };
    expect(FailedEventSchema.safeParse(data).success).toBe(true);
  });
});

describe("StreamingEventSchema (discriminated union)", () => {
  test("dispatches started event", () => {
    const data = {
      event: "started",
      review_id: "abc",
      summary: "x",
      call_to_action: [],
    };
    const result = StreamingEventSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.event).toBe("started");
  });

  test("dispatches token event", () => {
    const data = { event: "token", field: "summary", text: "hello" };
    const result = StreamingEventSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.event).toBe("token");
  });

  test("dispatches clause_evaluated event", () => {
    const data = {
      event: "clause_evaluated",
      clause: {
        section_number: "1.1",
        clause_type: "Term",
        severity: 1,
        fairness: "fair",
      },
    };
    const result = StreamingEventSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.event).toBe("clause_evaluated");
  });

  test("dispatches completed event", () => {
    const data = {
      event: "completed",
      result: {
        overall_fairness: "fair",
        agreement_type: "NDA",
        summary: "ok",
        call_to_action: [],
        clauses: [],
      },
    };
    const result = StreamingEventSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.event).toBe("completed");
  });

  test("dispatches rejected event", () => {
    const data = { event: "rejected", reason: "Not a contract" };
    const result = StreamingEventSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.event).toBe("rejected");
  });

  test("dispatches failed event", () => {
    const data = { event: "failed", reason: "error" };
    const result = StreamingEventSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.event).toBe("failed");
  });

  test("rejects unknown event type", () => {
    const data = { event: "unknown_event", foo: "bar" };
    expect(StreamingEventSchema.safeParse(data).success).toBe(false);
  });
});
