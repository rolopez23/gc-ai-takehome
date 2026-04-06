import type {
  FairnessRating,
  ReviewClause,
} from "@/app/evaluate-contract/types";

const FAIRNESS_BORDER: Record<FairnessRating, string> = {
  fair: "border-fair-border",
  "non-standard": "border-unfair-border",
  dealbreaker: "border-egregious-border",
};

const CARD = "rounded-lg border border-foreground/10 p-4";
const SECTION_HEADER = "flex items-baseline gap-2";
const SECTION_NUMBER = "text-sm font-medium text-foreground/50";
const CLAUSE_TYPE = "font-semibold";
const SEVERITY_BADGE = "text-xs font-medium text-foreground/50";
const EXPLANATION = "mt-2 text-sm text-foreground/70";

export default function ClauseCard({
  clause,
  fairness,
}: {
  clause: ReviewClause;
  fairness: FairnessRating;
}) {
  return (
    <div className={`${CARD} border-l-2 ${FAIRNESS_BORDER[fairness]}`}>
      <h4 className={SECTION_HEADER}>
        <span className={SECTION_NUMBER}>{clause.section_number}</span>
        <span className={CLAUSE_TYPE}>{clause.clause_type}</span>
        {clause.severity != null && (
          <span className={SEVERITY_BADGE}>Severity: {clause.severity}/10</span>
        )}
      </h4>
      <p className={EXPLANATION}>{clause.explanation}</p>
    </div>
  );
}
