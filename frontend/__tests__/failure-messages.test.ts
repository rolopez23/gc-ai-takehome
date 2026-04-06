import { describe, test, expect } from "vitest";
import {
  FAILURE_MESSAGES,
  getFailureMessage,
} from "@/app/evaluate-contract/failure-messages";

describe("FAILURE_MESSAGES", () => {
  test("all 5 failure codes have entries", () => {
    const expectedCodes = [
      "too_large",
      "timeout",
      "anthropic_error",
      "parse_error",
      "unknown",
    ];
    for (const code of expectedCodes) {
      expect(FAILURE_MESSAGES[code]).toBeDefined();
    }
  });

  test("known code returns correct message", () => {
    expect(getFailureMessage("timeout")).toBe(
      "The evaluation timed out. Please try again.",
    );
  });

  test("unknown code falls back to generic message", () => {
    expect(getFailureMessage("new_code")).toBe(FAILURE_MESSAGES.unknown);
  });

  test("null falls back to generic message", () => {
    expect(getFailureMessage(null)).toBe(FAILURE_MESSAGES.unknown);
  });

  test("undefined falls back to generic message", () => {
    expect(getFailureMessage(undefined)).toBe(FAILURE_MESSAGES.unknown);
  });
});
