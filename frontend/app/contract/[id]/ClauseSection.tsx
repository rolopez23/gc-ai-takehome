'use client';

import { useState } from 'react';
import type { FairnessRating, EvalClause } from '../../evaluate-contract/types';
import { getFairnessDisplay } from '../../evaluate-contract/fairness-utils';
import ClauseCard from './ClauseCard';

interface ClauseSectionProps {
  rating: FairnessRating;
  clauses: EvalClause[];
}

export default function ClauseSection({ rating, clauses }: ClauseSectionProps) {
  const [expanded, setExpanded] = useState(false);
  const { label } = getFairnessDisplay(rating);

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between rounded-lg border border-foreground/10 px-4 py-3 text-left hover:bg-foreground/5"
      >
        <span className="font-semibold">{label} ({clauses.length})</span>
        <span className="text-foreground/40">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <div className="mt-2 space-y-2">
          {clauses.map((clause) => (
            <ClauseCard key={clause.section_number} clause={clause} />
          ))}
        </div>
      )}
    </div>
  );
}
