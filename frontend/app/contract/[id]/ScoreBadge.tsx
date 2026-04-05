import type { FairnessRating } from '@/app/evaluate-contract/types';
import { getFairnessDisplay } from '@/app/evaluate-contract/fairness-utils';

const BADGE_STYLING = 'inline-block rounded-full border px-3 py-1 text-sm font-semibold';

export default function ScoreBadge({ rating }: { rating: FairnessRating }) {
  const { label, colorClass } = getFairnessDisplay(rating);
  return (
    <span className={`${BADGE_STYLING} ${colorClass}`}>
      {label}
    </span>
  );
}
