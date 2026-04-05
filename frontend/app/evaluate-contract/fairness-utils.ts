import type { FairnessRating } from './types';

interface FairnessDisplay {
  label: string;
  colorClass: string;
}

export const COLORS = {
  fail: 'text-red-600 bg-red-50 border-red-200',
  warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  pass: 'text-green-600 bg-green-50 border-green-200',
} as const;

const FAIRNESS_DISPLAY: Record<FairnessRating, FairnessDisplay> = {
  dealbreaker: { label: 'Egregious', colorClass: COLORS.fail },
  'non-standard': { label: 'Unfair', colorClass: COLORS.warning },
  fair: { label: 'Fair', colorClass: COLORS.pass },
};

export function getFairnessDisplay(rating: FairnessRating): FairnessDisplay {
  return FAIRNESS_DISPLAY[rating];
}

export const FAIRNESS_SECTION_ORDER: readonly FairnessRating[] = ['dealbreaker', 'non-standard', 'fair'];
