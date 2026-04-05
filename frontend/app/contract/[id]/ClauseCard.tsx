import type { EvalClause } from '../../evaluate-contract/types';

export default function ClauseCard({ clause }: { clause: EvalClause }) {
  return (
    <div className="rounded-lg border border-foreground/10 p-4">
      <div className="flex items-baseline gap-2">
        <span className="text-sm font-medium text-foreground/50">{clause.section_number}</span>
        <span className="font-semibold">{clause.clause_type}</span>
      </div>
      <p className="mt-2 text-sm text-foreground/70">{clause.explanation}</p>
    </div>
  );
}
