import type { FairnessRating } from '@/app/evaluate-contract/types';

interface FairnessDisplay {
  label: string;
  colorClass: string;
}

export const COLORS = {
  fail: 'text-egregious-fg bg-egregious-bg border-egregious-border',
  warning: 'text-unfair-fg bg-unfair-bg border-unfair-border',
  pass: 'text-fair-fg bg-fair-bg border-fair-border',
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
