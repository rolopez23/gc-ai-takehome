'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import type { ReviewResponse, ReviewCompleted, ReviewClause, FairnessRating } from '../../evaluate-contract/types';
import { ReviewResponseSchema } from '../../evaluate-contract/types';
import { FAIRNESS_SECTION_ORDER } from '../../evaluate-contract/fairness-utils';
import ScoreBadge from './ScoreBadge';
import ClauseSection from './ClauseSection';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const POLL_INTERVAL = 2000;

const PAGE_CONTAINER = 'mx-auto max-w-2xl px-4 py-12';
const BACK_LINK = 'mt-6 inline-block text-sm text-foreground/60 underline hover:text-foreground';

const STATUS_TEXT: Record<string, string> = {
  pending: 'Preparing evaluation...',
  reading: 'Reading document...',
  evaluating: 'Evaluating contract...',
};

const HEIGHT = { '3.5': 'h-3.5', '4': 'h-4', '5': 'h-5', '8': 'h-8' } as const;
const WIDTH = { '14': 'w-14', '20': 'w-20', '28': 'w-28', '32': 'w-32', '2/3': 'w-2/3', '3/4': 'w-3/4', '4/5': 'w-4/5', '5/6': 'w-5/6', 'full': 'w-full' } as const;

function ShimmerBar({ h, w, pill }: { h: keyof typeof HEIGHT; w: keyof typeof WIDTH; pill?: boolean }) {
  return (
    <div className={`animate-pulse bg-foreground/[0.06] ${HEIGHT[h]} ${WIDTH[w]} ${pill ? 'rounded-full' : 'rounded'}`} />
  );
}

function LoadingState({ statusText }: { statusText: string }) {
  return (
    <div className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluating contract</h1>
      <div data-testid="loading-shimmer" className="mt-6 space-y-6" role="status">
        <p className="sr-only">Evaluating contract, please wait...</p>
        <p className="text-sm text-foreground/60" data-testid="status-text">{statusText}</p>
        <div className="space-y-3">
          <ShimmerBar h="8" w="28" pill />
          <ShimmerBar h="4" w="full" />
          <ShimmerBar h="4" w="4/5" />
        </div>
        <div className="space-y-2 border-l-2 border-foreground/[0.06] pl-4">
          <ShimmerBar h="3.5" w="3/4" />
          <ShimmerBar h="3.5" w="2/3" />
        </div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-2.5 rounded-lg border border-foreground/[0.06] p-4">
            <div className="flex items-center gap-3">
              <ShimmerBar h="5" w="14" />
              <ShimmerBar h="5" w="32" />
              <div className="ml-auto"><ShimmerBar h="5" w="20" pill /></div>
            </div>
            <ShimmerBar h="3.5" w="full" />
            <ShimmerBar h="3.5" w="5/6" />
          </div>
        ))}
      </div>
    </div>
  );
}

function groupByFairness(clauses: ReviewClause[]) {
  return clauses.reduce<Record<FairnessRating, ReviewClause[]>>(
    (groups, clause) => {
      groups[clause.fairness].push(clause);
      return groups;
    },
    { dealbreaker: [], 'non-standard': [], fair: [] },
  );
}

function NoEvaluation() {
  return (
    <div className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">No evaluation found</h1>
      <p className="mt-2 text-foreground/60">This evaluation may have expired or the link is invalid.</p>
      <Link href="/evaluate-contract" className={BACK_LINK}>
        Evaluate a contract
      </Link>
    </div>
  );
}

function EvaluationResults({ result }: { result: ReviewCompleted }) {
  const grouped = groupByFairness(result.clauses);

  return (
    <article className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluation complete</h1>
      {result.overall_fairness && (
        <div className="mt-4">
          <ScoreBadge rating={result.overall_fairness} />
        </div>
      )}
      {result.summary && <p className="mt-3 text-foreground/60">{result.summary}</p>}
      {result.call_to_action && (
        <ul className="mt-3 list-disc pl-5 text-sm text-foreground/70">
          {result.call_to_action.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      )}
      <div className="mt-6 space-y-3">
        {FAIRNESS_SECTION_ORDER.map((rating) => (
          <ClauseSection key={rating} rating={rating} clauses={grouped[rating]} />
        ))}
      </div>
      <Link href="/evaluate-contract" className={BACK_LINK}>
        Evaluate another contract
      </Link>
    </article>
  );
}

function NotAContract({ summary }: { summary: string | null }) {
  return (
    <div className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">Not a contract</h1>
      <p className="mt-2 text-foreground/60">{summary || 'The uploaded document does not appear to be a contract.'}</p>
      <Link href="/evaluate-contract" className={BACK_LINK}>
        Try another document
      </Link>
    </div>
  );
}

function EvaluationFailed({ message }: { message: string }) {
  return (
    <div className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluation failed</h1>
      <p className="mt-2 text-foreground/60">{message}</p>
      <Link href="/evaluate-contract" className={BACK_LINK}>
        Try again
      </Link>
    </div>
  );
}

export default function ContractPage() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [statusText, setStatusText] = useState('Preparing evaluation...');

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function fetchAndPoll() {
      try {
        while (!cancelled) {
          const res = await fetch(`${BACKEND_URL}/api/contracts/${id}/review`, {
            signal: controller.signal,
          });
          if (res.status === 404) {
            setNotFound(true);
            setLoading(false);
            return;
          }
          if (!res.ok) throw new Error('Failed to fetch review');
          const data = ReviewResponseSchema.parse(await res.json());
          setReview(data);
          if (data.status === 'completed' || data.status === 'failed') {
            setLoading(false);
            return;
          }
          setStatusText(STATUS_TEXT[data.status] || 'Processing...');
          await new Promise((r) => setTimeout(r, POLL_INTERVAL));
        }
      } catch (e) {
        if (!cancelled) {
          setNotFound(true);
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
  if (!review) return <NoEvaluation />;
  if (review.status === 'failed') return <EvaluationFailed message={review.failure_message} />;
  if (review.status === 'completed') {
    if (review.overall_fairness) return <EvaluationResults result={review} />;
    return <NotAContract summary={review.summary} />;
  }
  return <LoadingState statusText={statusText} />;
}
