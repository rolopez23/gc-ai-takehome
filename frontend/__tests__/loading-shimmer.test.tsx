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

const POLLING_RESPONSE = {
  id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
  contract_id: "452be08b-a29d-402f-8f44-6b1a0f976efa",
  status: "evaluating",
};

beforeEach(() => {
  vi.restoreAllMocks();
});

async function stageFileAndSubmit(fetchImpl: typeof fetch) {
  vi.stubGlobal("fetch", vi.fn(fetchImpl));
  render(<EvaluateContractPage />);
  const file = new File(["contract text"], "contract.txt", {
    type: "text/plain",
  });
  await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
  await userEvent.click(
    screen.getByRole("button", { name: /evaluate contract/i }),
  );
}

describe("Loading shimmer", () => {
  test("shows shimmer when submitting", async () => {
    // Upload resolves, poll hangs → shimmer stays visible
    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 201 }),
        );
      }
      return new Promise<Response>(() => {}); // poll hangs
    });

    await waitFor(() => {
      expect(screen.getByTestId("loading-shimmer")).toBeInTheDocument();
    });
  });

  test("disables button when submitting", async () => {
    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 201 }),
        );
      }
      return new Promise<Response>(() => {});
    });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /evaluate contract/i }),
      ).toBeDisabled();
    });
  });

  test("sends FormData to backend upload endpoint", async () => {
    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 201 }),
        );
      }
      return new Promise<Response>(() => {});
    });

    await waitFor(() => {
      const calls = (fetch as ReturnType<typeof vi.fn>).mock.calls;
      expect(calls[0][0]).toContain("/api/contracts/upload");
      expect(calls[0][1].method).toBe("POST");
      expect(calls[0][1].body).toBeInstanceOf(FormData);
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

  test("hides shimmer on failed evaluation", async () => {
    const failedReview = {
      id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
      status: "failed",
      failure_message: "timeout",
    };

    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 201 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify(failedReview), { status: 200 }),
      );
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading-shimmer")).not.toBeInTheDocument();
    });
  });
});
