"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileDropZone } from "@/app/evaluate-contract/FileDropZone";
import { LoadingShimmer } from "@/app/evaluate-contract/LoadingShimmer";
import { BACKEND_URL } from "@/app/evaluate-contract/constants";
import { UploadResponseSchema } from "@/app/evaluate-contract/types";
import { readNDJSONStream } from "@/app/evaluate-contract/stream";
import type { StreamClause } from "@/app/evaluate-contract/stream-types";

const ERROR_ALERT =
  "flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg";

async function uploadContract(
  file: File,
  instructions: string,
  signal: AbortSignal,
  stream = false,
) {
  const form = new FormData();
  form.append("file", file);
  if (instructions.trim()) form.append("instructions", instructions);
  const url = stream
    ? `${BACKEND_URL}/api/contracts/upload?stream=true`
    : `${BACKEND_URL}/api/contracts/upload`;
  const res = await fetch(url, {
    method: "POST",
    body: form,
    signal,
  });
  if (!res.ok) {
    if (res.status === 413) throw new Error("File too large (max 10MB)");
    if (res.status === 400) {
      const data = await res.json();
      throw new Error(data.detail || "Invalid file");
    }
    throw new Error("Upload failed");
  }
  return UploadResponseSchema.parse(await res.json());
}

async function consumeStream(
  contractId: string,
  reviewId: string,
  signal: AbortSignal,
  callbacks: {
    onStatus: (s: string) => void;
    onClause: (c: StreamClause) => void;
    onSummary: (s: string) => void;
  },
): Promise<{ navigateTo?: string; error?: string }> {
  const res = await fetch(`${BACKEND_URL}/api/reviews/${reviewId}/stream`, {
    signal,
  });
  if (!res.ok) throw new Error("Stream unavailable");

  let summaryBuffer = "";

  for await (const event of readNDJSONStream(res)) {
    if (signal.aborted) return {};

    switch (event.event) {
      case "started":
        callbacks.onStatus("Evaluating contract...");
        summaryBuffer = event.summary;
        callbacks.onSummary(event.summary);
        break;
      case "verifying":
        callbacks.onStatus("Verifying document...");
        break;
      case "splitting":
        callbacks.onStatus(
          `Splitting ${event.agreement_type} into ${event.clause_count} clauses...`,
        );
        break;
      case "token":
        if (event.field === "summary") {
          summaryBuffer += event.text;
          callbacks.onSummary(summaryBuffer);
        }
        callbacks.onStatus("Evaluating contract...");
        break;
      case "clause_evaluated":
        callbacks.onClause(event.clause);
        break;
      case "replace":
        if (event.field === "summary" && event.text !== undefined) {
          summaryBuffer = event.text;
          callbacks.onSummary(event.text);
        }
        break;
      case "completed":
        return { navigateTo: `/contract/${contractId}` };
      case "rejected":
        return { error: event.reason };
      case "failed":
        return { error: event.reason };
      case "clause_error":
        // Individual clause errors are non-fatal
        break;
    }
  }

  // Stream ended without a terminal event — treat as error
  return { error: "Stream ended unexpectedly. Please try again." };
}

export default function EvaluateContractPage() {
  const [file, setFile] = useState<File | null>(null);
  const [instructions, setInstructions] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusText, setStatusText] = useState("Preparing evaluation...");
  const [streamClauses, setStreamClauses] = useState<StreamClause[]>([]);
  const [streamSummary, setStreamSummary] = useState("");
  const router = useRouter();
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  async function handleSubmit() {
    if (!file) return;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setError(null);
    setIsLoading(true);
    setStatusText("Preparing evaluation...");
    setStreamClauses([]);
    setStreamSummary("");

    try {
      // Upload with stream flag
      const { contract_id, review_id } = await uploadContract(
        file,
        instructions,
        controller.signal,
        true,
      );

      const result = await consumeStream(
        contract_id,
        review_id,
        controller.signal,
        {
          onStatus: setStatusText,
          onClause: (c) => setStreamClauses((prev) => [...prev, c]),
          onSummary: setStreamSummary,
        },
      );

      if (result.navigateTo) {
        router.push(result.navigateTo);
        return;
      }
      if (result.error) {
        setError(result.error);
        setIsLoading(false);
        return;
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : "Something went wrong");
      setIsLoading(false);
    }
  }

  return (
    <div
      className="mx-auto max-w-2xl space-y-6 px-6 pt-12"
      aria-busy={isLoading}
    >
      <h1 className="text-2xl font-bold tracking-tight">Evaluate Contract</h1>

      {isLoading ? (
        <>
          <LoadingShimmer statusText={statusText} />
          {streamClauses.length > 0 && (
            <div data-testid="stream-clauses" className="space-y-3">
              {streamClauses.map((clause, i) => (
                <div
                  key={`${clause.section_number}-${i}`}
                  data-testid="stream-clause-card"
                  className="rounded-lg border border-foreground/[0.06] p-4 text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-foreground/50">
                      {clause.section_number}
                    </span>
                    <span className="font-medium">{clause.clause_type}</span>
                  </div>
                  {clause.explanation && (
                    <p className="mt-1 text-foreground/70">
                      {clause.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
          {streamSummary && (
            <p
              data-testid="stream-summary"
              className="text-sm text-foreground/70"
            >
              {streamSummary}
            </p>
          )}
        </>
      ) : (
        <>
          <FileDropZone file={file} onFileChange={setFile} />

          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Add any specific instructions for the evaluation..."
            rows={4}
            className="w-full rounded-lg border border-foreground/20 bg-transparent px-4 py-3 text-sm placeholder:text-foreground/40 focus:border-foreground/40 focus:outline-none"
          />
        </>
      )}

      <button
        type="button"
        disabled={!file || isLoading}
        onClick={handleSubmit}
        className="w-full sm:w-auto rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background disabled:opacity-40"
      >
        Evaluate Contract
      </button>

      {error && !isLoading && (
        <div className={ERROR_ALERT} role="alert">
          <span>⚠</span>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
