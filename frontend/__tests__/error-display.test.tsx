import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import EvaluateContractPage from "@/app/evaluate-contract/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

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

describe("Error display", () => {
  test("shows error on network failure", async () => {
    await stageFileAndSubmit(() => Promise.reject(new Error("network error")));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  test("shows error on 400 response", async () => {
    await stageFileAndSubmit(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: "Unsupported file type" }), {
          status: 400,
        }),
      ),
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  test("shows error on 413 response", async () => {
    await stageFileAndSubmit(() =>
      Promise.resolve(new Response("", { status: 413 })),
    );

    await waitFor(() => {
      expect(screen.getByText(/too large/i)).toBeInTheDocument();
    });
  });

  test("shows friendly error when evaluation fails with known failure_code", async () => {
    const uploadResponse = {
      contract_id: "452be08b-a29d-402f-8f44-6b1a0f976efa",
      review_id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
      status: "pending",
    };
    const failedReview = {
      id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
      status: "failed",
      failure_message: "API timeout",
      failure_code: "timeout",
    };

    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(uploadResponse), { status: 201 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify(failedReview), { status: 200 }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/timed out/i)).toBeInTheDocument();
    });
  });

  test("shows generic error when evaluation fails with null failure_code", async () => {
    const uploadResponse = {
      contract_id: "452be08b-a29d-402f-8f44-6b1a0f976efa",
      review_id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
      status: "pending",
    };
    const failedReview = {
      id: "a9198839-1da3-4fb3-ac30-c462cc81ee4e",
      status: "failed",
      failure_message: null,
      failure_code: null,
    };

    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(uploadResponse), { status: 201 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify(failedReview), { status: 200 }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });

  test("preserves file and instructions on error", async () => {
    await stageFileAndSubmit(() => Promise.reject(new Error("network error")));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText("contract.txt")).toBeInTheDocument();
  });
});
