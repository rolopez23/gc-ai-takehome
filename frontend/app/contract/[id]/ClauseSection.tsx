'use client';

import { useState } from 'react';
import type { FairnessRating, ReviewClause } from '@/app/evaluate-contract/types';
import { getFairnessDisplay } from '@/app/evaluate-contract/fairness-utils';
import ClauseCard from '@/app/contract/[id]/ClauseCard';

const SECTION_BORDER = 'rounded-lg border border-foreground/10 px-4 py-3';
const SECTION_HEADER = `flex w-full items-center justify-between ${SECTION_BORDER} text-left hover:bg-foreground/5`;
const CLAUSE_LIST = 'mt-2 max-h-[50vh] space-y-2 overflow-y-auto';

function NoClauses({ rating, label }: { rating: FairnessRating; label: string }) {
  const isCelebratory = rating !== 'fair';
  const icon = isCelebratory ? '✓' : '⚠';
  const text = isCelebratory
    ? `No ${label.toLowerCase()} clauses`
    : 'No fair clauses found';

  return (
    <div className={`flex items-center gap-2 ${SECTION_BORDER} text-foreground/50`}>
      <span>{icon}</span>
      <span>{text}</span>
    </div>
  );
}

function ExpandableClauses({ label, clauses }: { label: string; clauses: ReviewClause[] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <section aria-label={`${label} clauses`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        className={SECTION_HEADER}
      >
        <span className="font-semibold">{label} ({clauses.length})</span>
        <span className="text-foreground/40">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <ul className={CLAUSE_LIST}>
          {clauses.map((clause) => (
            <li key={clause.section_number}>
              <ClauseCard clause={clause} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

interface ClauseSectionProps {
  rating: FairnessRating;
  clauses: ReviewClause[];
}

export default function ClauseSection({ rating, clauses }: ClauseSectionProps) {
  const { label } = getFairnessDisplay(rating);

  if (clauses.length === 0) {
    return <NoClauses rating={rating} label={label} />;
  }

  return <ExpandableClauses label={label} clauses={clauses} />;
}
