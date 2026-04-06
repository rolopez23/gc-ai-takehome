"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type {
  ReviewResponse,
  ReviewCompleted,
  ReviewClause,
  FairnessRating,
} from "@/app/evaluate-contract/types";
import { ReviewResponseSchema } from "@/app/evaluate-contract/types";
import { FAIRNESS_SECTION_ORDER } from "@/app/evaluate-contract/fairness-utils";
import { LoadingShimmer } from "@/app/evaluate-contract/LoadingShimmer";
import {
  BACKEND_URL,
  POLL_INTERVAL,
  POLL_TIMEOUT,
  STATUS_TEXT,
} from "@/app/evaluate-contract/constants";
import { getFailureMessage } from "@/app/evaluate-contract/failure-messages";
import ScoreBadge from "@/app/contract/[id]/ScoreBadge";
import ClauseSection from "@/app/contract/[id]/ClauseSection";

const PAGE_CONTAINER = "mx-auto max-w-2xl px-6 pt-12";
const PAGE_TITLE = "text-2xl font-bold tracking-tight";
const BACK_LINK =
  "mt-6 inline-block text-sm text-muted underline hover:text-foreground";
const ERROR_ALERT =
  "flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg";

function LoadingState({ statusText }: { statusText: string }) {
  return (
    <div className={PAGE_CONTAINER}>
      <h1 className={PAGE_TITLE}>Evaluating contract</h1>
      <div className="mt-6">
        <LoadingShimmer statusText={statusText} />
      </div>
    </div>
  );
}

function groupByFairness(clauses: ReviewClause[]) {
  const groups: Record<string, ReviewClause[]> = {
    dealbreaker: [],
    "non-standard": [],
    fair: [],
    absent: [],
  };
  for (const clause of clauses) {
    if (clause.playbook_status === "ABSENT" || clause.is_synthetic) {
      groups.absent.push(clause);
    } else if (clause.fairness && clause.fairness in groups) {
      groups[clause.fairness].push(clause);
    } else {
      // Unknown fairness — default to non-standard
      groups["non-standard"].push(clause);
    }
  }
  for (const rating of Object.keys(groups)) {
    groups[rating].sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));
  }
  return groups;
}

function NoEvaluation() {
  return (
    <div className="mx-auto max-w-2xl px-6 flex min-h-[60vh] flex-col items-center justify-center text-center">
      <span className="text-2xl text-muted">◆</span>
      <h1 className="text-2xl font-bold mt-4">No evaluation found</h1>
      <p className="mt-2 text-sm text-muted max-w-sm">
        This evaluation may have expired or the link is invalid.
      </p>
      <Link
        href="/evaluate-contract"
        className="mt-6 rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background"
      >
        Evaluate a contract
      </Link>
    </div>
  );
}

function EvaluationResults({ result }: { result: ReviewCompleted }) {
  const grouped = groupByFairness(result.clauses);

  return (
    <article className={PAGE_CONTAINER}>
      <div className="sticky top-0 z-10 -mx-6 bg-background/95 backdrop-blur-sm px-6 pb-4 pt-12 -mt-12">
        <h1 className={PAGE_TITLE}>Evaluation complete</h1>
        {result.overall_fairness && (
          <div className="mt-2">
            <ScoreBadge rating={result.overall_fairness} />
          </div>
        )}
      </div>
      {result.summary && (
        <div className="mt-4 rounded-r-lg border-l-2 border-foreground/20 bg-surface py-3 pl-4 pr-4">
          <p className="text-sm text-muted">{result.summary}</p>
        </div>
      )}
      {result.call_to_action && (
        <ul className="mt-3 list-disc pl-5 text-sm text-muted">
          {result.call_to_action.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )}
      <div className="mt-6 space-y-3">
        {FAIRNESS_SECTION_ORDER.map((rating) => (
          <ClauseSection
            key={rating}
            rating={rating}
            clauses={grouped[rating]}
          />
        ))}
        {grouped.absent.length > 0 && (
          <ClauseSection
            rating={"absent" as FairnessRating}
            clauses={grouped.absent}
            title={`Missing from Contract (${grouped.absent.length})`}
          />
        )}
      </div>
      <Link href="/evaluate-contract" className={BACK_LINK}>
        Evaluate another contract
      </Link>
    </article>
  );
}

function NotAContract({ summary }: { summary: string | null }) {
  return (
    <div className="mx-auto max-w-2xl px-6 flex min-h-[60vh] flex-col items-center justify-center text-center">
      <span className="text-2xl text-muted">◆</span>
      <h1 className="text-2xl font-bold mt-4">Not a contract</h1>
      <p className="mt-2 text-sm text-muted max-w-sm">
        {summary || "The uploaded document does not appear to be a contract."}
      </p>
      <Link
        href="/evaluate-contract"
        className="mt-6 rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background"
      >
        Try another document
      </Link>
    </div>
  );
}

function EvaluationFailed({ message }: { message: string }) {
  return (
    <div className={PAGE_CONTAINER}>
      <h1 className={PAGE_TITLE}>Evaluation failed</h1>
      <div className={`mt-4 ${ERROR_ALERT}`} role="alert">
        <span>⚠</span>
        <p>{message}</p>
      </div>
      <Link
        href="/evaluate-contract"
        className="mt-6 inline-block rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background"
      >
        Try again
      </Link>
    </div>
  );
}

export default function ContractPage() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [statusText, setStatusText] = useState("Preparing evaluation...");

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const start = Date.now();

    async function fetchAndPoll() {
      try {
        while (!cancelled && Date.now() - start < POLL_TIMEOUT) {
          const res = await fetch(`${BACKEND_URL}/api/contracts/${id}/review`, {
            signal: controller.signal,
          });
          if (res.status === 404) {
            setNotFound(true);
            setLoading(false);
            return;
          }
          if (!res.ok) throw new Error("Failed to fetch review");
          const data = ReviewResponseSchema.parse(await res.json());
          setReview(data);
          if (
            data.status === "completed" ||
            data.status === "failed" ||
            data.status === "rejected"
          ) {
            setLoading(false);
            return;
          }
          setStatusText(STATUS_TEXT[data.status] || "Processing...");
          await new Promise((r) => setTimeout(r, POLL_INTERVAL));
        }
        if (!cancelled) {
          setError("Evaluation timed out — please try again");
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          if (e instanceof DOMException && e.name === "AbortError") return;
          setError(
            "Connection error — please check your network and try again",
          );
          setLoading(false);
        }
      }
    }

    fetchAndPoll();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [id]);

  if (loading) return <LoadingState statusText={statusText} />;
  if (notFound) return <NoEvaluation />;
  if (error) return <EvaluationFailed message={error} />;
  if (!review) return <NoEvaluation />;
  if (review.status === "failed")
    return (
      <EvaluationFailed message={getFailureMessage(review.failure_code)} />
    );
  if (review.status === "rejected")
    return (
      <NotAContract summary={"summary" in review ? review.summary : null} />
    );
  if (review.status === "completed") {
    if (review.overall_fairness) return <EvaluationResults result={review} />;
    return <NotAContract summary={review.summary} />;
  }
  return <LoadingState statusText={statusText} />;
}
