import type { FairnessRating } from '../../evaluate-contract/types';
import { getFairnessDisplay } from '../../evaluate-contract/fairness-utils';

export default function ScoreBadge({ rating }: { rating: FairnessRating }) {
  const { label, colorClass } = getFairnessDisplay(rating);
  return (
    <span className={`inline-block rounded-full border px-3 py-1 text-sm font-semibold ${colorClass}`}>
      {label}
    </span>
  );
}
