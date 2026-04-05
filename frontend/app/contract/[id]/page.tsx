'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEvalResult } from '../../evaluate-contract/eval-result-context';
import type { EvalSuccess } from '../../evaluate-contract/types';
import ScoreBadge from './ScoreBadge';

const PAGE_CONTAINER = 'mx-auto max-w-2xl px-4 py-12';

function asSuccess(raw: ReturnType<ReturnType<typeof useEvalResult>['getResult']>): EvalSuccess | undefined {
  return raw && raw.error === null ? raw : undefined;
}

export default function ContractPage() {
  const { id } = useParams<{ id: string }>();
  const { getResult } = useEvalResult();
  const result = asSuccess(getResult(id));

  if (!result) {
    return (
      <div className={PAGE_CONTAINER}>
        <h1 className="text-3xl font-bold tracking-tight">No evaluation found</h1>
        <p className="mt-2 text-foreground/60">This evaluation may have expired or the link is invalid.</p>
      </div>
    );
  }

  return (
    <div className={PAGE_CONTAINER}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluation complete</h1>
      <div className="mt-4">
        <ScoreBadge rating={result.overall_fairness} />
      </div>
      <p className="mt-3 text-foreground/60">{result.summary}</p>
      <Link href="/evaluate-contract" className="mt-6 inline-block text-sm text-foreground/60 underline hover:text-foreground">
        Evaluate another contract
      </Link>
    </div>
  );
}
