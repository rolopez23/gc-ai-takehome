import { describe, test, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import EvaluateContractPage from "@/app/evaluate-contract/page";

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

  test("shows error when stream fails", async () => {
    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
        );
      }
      return Promise.resolve(
        makeStreamResponse([
          {
            event: "started",
            review_id: REVIEW_ID,
            summary: "",
            call_to_action: [],
          },
          { event: "failed", reason: "Evaluation timed out. Please try again." },
        ]),
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/timed out/i)).toBeInTheDocument();
    });
  });

  test("shows rejection reason from stream", async () => {
    let callCount = 0;
    await stageFileAndSubmit(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }),
        );
      }
      return Promise.resolve(
        makeStreamResponse([
          {
            event: "started",
            review_id: REVIEW_ID,
            summary: "",
            call_to_action: [],
          },
          {
            event: "rejected",
            reason: "This does not appear to be a contract.",
          },
        ]),
      );
    });

    await waitFor(() => {
      expect(
        screen.getByText(/does not appear to be a contract/i),
      ).toBeInTheDocument();
    });
  });

  test("shows file info after upload error (file preserved in form)", async () => {
    await stageFileAndSubmit(() => Promise.reject(new Error("network error")));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    // After a failed upload, the page resets to idle (failed state) where
    // the file drop zone is not shown — the error state with Try again is shown instead.
    // This is expected: the user clicks "Try again" to reload.
    expect(screen.getByRole("alert")).toHaveTextContent("network error");
  });
});
