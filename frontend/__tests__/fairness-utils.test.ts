import { describe, it, expect } from 'vitest';
import { getFairnessDisplay, FAIRNESS_SECTION_ORDER, COLORS } from '@/app/evaluate-contract/fairness-utils';

describe('getFairnessDisplay', () => {
  it('maps dealbreaker to Egregious with fail styling', () => {
    const display = getFairnessDisplay('dealbreaker');
    expect(display.label).toBe('Egregious');
    expect(display.colorClass).toBe(COLORS.fail);
  });

  it('maps non-standard to Unfair with warning styling', () => {
    const display = getFairnessDisplay('non-standard');
    expect(display.label).toBe('Unfair');
    expect(display.colorClass).toBe(COLORS.warning);
  });

  it('maps fair to Fair with pass styling', () => {
    const display = getFairnessDisplay('fair');
    expect(display.label).toBe('Fair');
    expect(display.colorClass).toBe(COLORS.pass);
  });
});

describe('FAIRNESS_SECTION_ORDER', () => {
  it('lists tiers in severity order: dealbreaker, non-standard, fair', () => {
    expect(FAIRNESS_SECTION_ORDER).toEqual(['dealbreaker', 'non-standard', 'fair']);
  });
});
