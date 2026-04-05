import type { ReviewClause } from '@/app/evaluate-contract/types';

const CARD = 'rounded-lg border border-foreground/10 p-4';
const SECTION_HEADER = 'flex items-baseline gap-2';
const SECTION_NUMBER = 'text-sm font-medium text-foreground/50';
const CLAUSE_TYPE = 'font-semibold';
const EXPLANATION = 'mt-2 text-sm text-foreground/70';

export default function ClauseCard({ clause }: { clause: ReviewClause }) {
  return (
    <div className={CARD}>
      <h4 className={SECTION_HEADER}>
        <span className={SECTION_NUMBER}>{clause.section_number}</span>
        <span className={CLAUSE_TYPE}>{clause.clause_type}</span>
      </h4>
      <p className={EXPLANATION}>{clause.explanation}</p>
    </div>
  );
}
