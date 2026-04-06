"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileDropZone } from "@/app/evaluate-contract/FileDropZone";
import {
  useContractStream,
  type StreamStage,
} from "@/app/evaluate-contract/useContractStream";
import type { StreamClause } from "@/app/evaluate-contract/stream-types";
import { getFairnessDisplay } from "@/app/evaluate-contract/fairness-utils";

const ERROR_ALERT =
  "flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg";

function stageHeadline(
  stage: StreamStage,
  agreementType: string | null,
  totalClauses: number,
  evaluatedCount: number,
): string {
  switch (stage) {
    case "uploading":
      return "Uploading document...";
    case "verifying":
      return "Verifying document...";
    case "splitting":
      return totalClauses > 0
        ? `Splitting ${agreementType ?? "contract"} into ${totalClauses} clauses...`
        : "Splitting into clauses...";
    case "evaluating":
      return totalClauses > 0
        ? `Evaluating clauses (${evaluatedCount}/${totalClauses})...`
        : "Evaluating clauses...";
    case "summarizing":
      return "Generating summary...";
    default:
      return "Processing...";
  }
}

function StatsDot({ color }: { color: string }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${color}`}
      aria-hidden="true"
    />
  );
}

function StatsBar({
  buckets,
}: {
  buckets: { dealbreaker: number; nonStandard: number; fair: number };
}) {
  return (
    <div
      data-testid="stats-bar"
      className="flex items-center justify-center gap-6 rounded-lg border border-foreground/[0.06] px-6 py-3 text-sm"
    >
      <span className="flex items-center gap-2">
        <StatsDot color="bg-egregious-fg" />
        <span className="text-foreground/70">Dealbreaker:</span>
        <span className="font-semibold" data-testid="stat-dealbreaker">
          {buckets.dealbreaker}
        </span>
      </span>
      <span className="flex items-center gap-2">
        <StatsDot color="bg-unfair-fg" />
        <span className="text-foreground/70">Non-Standard:</span>
        <span className="font-semibold" data-testid="stat-nonstandard">
          {buckets.nonStandard}
        </span>
      </span>
      <span className="flex items-center gap-2">
        <StatsDot color="bg-fair-fg" />
        <span className="text-foreground/70">Fair:</span>
        <span className="font-semibold" data-testid="stat-fair">
          {buckets.fair}
        </span>
      </span>
    </div>
  );
}

function ClausePreview({ clause }: { clause: StreamClause }) {
  const { label, colorClass } = getFairnessDisplay(clause.fairness);
  const findingText = clause.finding || clause.explanation || "Evaluating...";

  return (
    <div
      data-testid="clause-preview"
      className="rounded-lg border border-foreground/[0.06] p-4 text-sm animate-[fadeIn_200ms_ease-out]"
    >
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs text-foreground/50">
          {clause.section_number}
        </span>
        <span className="font-medium">{clause.clause_type}</span>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span
          className={`inline-block rounded-full border px-2 py-0.5 text-xs font-semibold ${colorClass}`}
        >
          {label}
        </span>
        {clause.severity != null && (
          <span className="text-xs text-foreground/50">
            Severity: {clause.severity}/10
          </span>
        )}
      </div>
      <p className="mt-2 text-foreground/70 line-clamp-2">{findingText}</p>
    </div>
  );
}

function ProgressBar({
  evaluated,
  total,
}: {
  evaluated: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((evaluated / total) * 100) : 0;

  return (
    <div data-testid="progress-bar" className="space-y-1.5">
      <p className="text-center text-xs text-foreground/50">
        Evaluated {evaluated} of {total} clauses
      </p>
      <div className="h-1.5 w-full rounded-full bg-foreground/[0.06] overflow-hidden">
        <div
          className="h-full rounded-full bg-foreground/30 transition-all duration-300 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function StreamingView({
  stage,
  agreementType,
  totalClauses,
  evaluatedCount,
  buckets,
  lastClause,
}: {
  stage: StreamStage;
  agreementType: string | null;
  totalClauses: number;
  evaluatedCount: number;
  buckets: { dealbreaker: number; nonStandard: number; fair: number };
  lastClause: StreamClause | null;
}) {
  const headline = stageHeadline(
    stage,
    agreementType,
    totalClauses,
    evaluatedCount,
  );
  const showStats =
    stage === "evaluating" || stage === "summarizing" || stage === "completed";
  const showProgress = stage === "evaluating" && totalClauses > 0;

  return (
    <div
      data-testid="streaming-view"
      className="streaming-bg min-h-[40vh] rounded-xl p-8 space-y-6"
      role="status"
    >
      <p className="sr-only">Evaluating contract, please wait...</p>

      <h2
        data-testid="stage-headline"
        className="text-center text-lg font-semibold tracking-tight animate-pulse"
      >
        {headline}
      </h2>

      {showStats && <StatsBar buckets={buckets} />}

      {lastClause && <ClausePreview clause={lastClause} />}

      {showProgress && (
        <ProgressBar evaluated={evaluatedCount} total={totalClauses} />
      )}
    </div>
  );
}

export default function EvaluateContractPage() {
  const [file, setFile] = useState<File | null>(null);
  const [instructions, setInstructions] = useState("");
  const { state, startStream } = useContractStream();
  const router = useRouter();

  const isStreaming =
    state.stage !== "idle" &&
    state.stage !== "completed" &&
    state.stage !== "failed" &&
    state.stage !== "rejected";

  useEffect(() => {
    if (state.stage === "completed" && state.contractId) {
      router.push(`/contract/${state.contractId}`);
    }
  }, [state.stage, state.contractId, router]);

  async function handleSubmit() {
    if (!file) return;
    await startStream(file, instructions);
  }

  return (
    <div
      className="mx-auto max-w-2xl space-y-6 px-6 pt-12"
      aria-busy={isStreaming}
    >
      <h1 className="text-2xl font-bold tracking-tight">Evaluate Contract</h1>

      {isStreaming ? (
        <StreamingView
          stage={state.stage}
          agreementType={state.agreementType}
          totalClauses={state.totalClauses}
          evaluatedCount={state.evaluatedCount}
          buckets={state.buckets}
          lastClause={state.lastClause}
        />
      ) : state.stage === "rejected" ? (
        <div className="space-y-4">
          <div className={ERROR_ALERT} role="alert">
            <span>&#9888;</span>
            <p>{state.error}</p>
          </div>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background"
          >
            Try another
          </button>
        </div>
      ) : state.stage === "failed" ? (
        <div className="space-y-4">
          <div className={ERROR_ALERT} role="alert">
            <span>&#9888;</span>
            <p>{state.error}</p>
          </div>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background"
          >
            Try again
          </button>
        </div>
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

          <button
            type="button"
            disabled={!file || isStreaming}
            onClick={handleSubmit}
            className="w-full sm:w-auto rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background disabled:opacity-40"
          >
            Evaluate Contract
          </button>
        </>
      )}
    </div>
  );
}
