import type { FairnessRating } from './types';

interface FairnessDisplay {
  label: string;
  colorClass: string;
}

const FAIRNESS_DISPLAY: Record<FairnessRating, FairnessDisplay> = {
  dealbreaker: { label: 'Egregious', colorClass: 'text-red-600 bg-red-50 border-red-200' },
  'non-standard': { label: 'Unfair', colorClass: 'text-yellow-600 bg-yellow-50 border-yellow-200' },
  fair: { label: 'Fair', colorClass: 'text-green-600 bg-green-50 border-green-200' },
};

export function getFairnessDisplay(rating: FairnessRating): FairnessDisplay {
  return FAIRNESS_DISPLAY[rating];
}
