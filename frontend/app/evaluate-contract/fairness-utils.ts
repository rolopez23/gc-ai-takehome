import type { FairnessRating } from "@/app/evaluate-contract/types";

interface FairnessDisplay {
  label: string;
  colorClass: string;
}

export const COLORS = {
  fail: "text-egregious-fg bg-egregious-bg border-egregious-border",
  warning: "text-unfair-fg bg-unfair-bg border-unfair-border",
  pass: "text-fair-fg bg-fair-bg border-fair-border",
} as const;

const FAIRNESS_DISPLAY: Record<FairnessRating, FairnessDisplay> = {
  dealbreaker: { label: "Dealbreaker", colorClass: COLORS.fail },
  "non-standard": { label: "Non-Standard", colorClass: COLORS.warning },
  fair: { label: "Standard", colorClass: COLORS.pass },
};

const ABSENT_DISPLAY: FairnessDisplay = {
  label: "Missing",
  colorClass: "text-foreground/50 bg-foreground/5 border-foreground/10",
};

export function getFairnessDisplay(
  rating: FairnessRating | string,
): FairnessDisplay {
  if (rating in FAIRNESS_DISPLAY)
    return FAIRNESS_DISPLAY[rating as FairnessRating];
  if (rating === "absent") return ABSENT_DISPLAY;
  return { label: rating, colorClass: COLORS.warning };
}

export const FAIRNESS_SECTION_ORDER: readonly FairnessRating[] = [
  "dealbreaker",
  "non-standard",
  "fair",
];
