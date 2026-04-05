'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEvalResult } from '../../evaluate-contract/eval-result-context';
import { FAIRNESS_SECTION_ORDER } from '../../evaluate-contract/fairness-utils';
import type { EvalSuccess, EvalClause, FairnessRating } from '../../evaluate-contract/types';
import ScoreBadge from './ScoreBadge';
import ClauseSection from './ClauseSection';

const PAGE_CONTAINER = 'mx-auto max-w-2xl px-4 py-12';
const BACK_LINK = 'mt-6 inline-block text-sm text-foreground/60 underline hover:text-foreground';

function asSuccess(raw: ReturnType<ReturnType<typeof useEvalResult>['getResult']>): EvalSuccess | undefined {
  return raw && raw.error === null ? raw : undefined;
}

function groupByFairness(clauses: EvalClause[]) {
  return clauses.reduce<Record<FairnessRating, EvalClause[]>>(
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
    </div>
  );
}

function EvaluationResults({ result }: { result: EvalSuccess }) {
  const grouped = groupByFairness(result.clauses);

  return (
    <article className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluation complete</h1>
      <div className="mt-4">
        <ScoreBadge rating={result.overall_fairness} />
      </div>
      <p className="mt-3 text-foreground/60">{result.summary}</p>
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

export default function ContractPage() {
  const { id } = useParams<{ id: string }>();
  const { getResult } = useEvalResult();
  const result = asSuccess(getResult(id));

  if (!result) return <NoEvaluation />;

  return <EvaluationResults result={result} />;
}
