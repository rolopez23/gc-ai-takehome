import { describe, it, expect } from 'vitest';
import { getFairnessDisplay, FAIRNESS_SECTION_ORDER } from '@/app/evaluate-contract/fairness-utils';

describe('getFairnessDisplay', () => {
  it('maps dealbreaker to Egregious with red styling', () => {
    const display = getFairnessDisplay('dealbreaker');
    expect(display.label).toBe('Egregious');
    expect(display.colorClass).toContain('text-red-600');
  });

  it('maps non-standard to Unfair with yellow styling', () => {
    const display = getFairnessDisplay('non-standard');
    expect(display.label).toBe('Unfair');
    expect(display.colorClass).toContain('text-yellow-600');
  });

  it('maps fair to Fair with green styling', () => {
    const display = getFairnessDisplay('fair');
    expect(display.label).toBe('Fair');
    expect(display.colorClass).toContain('text-green-600');
  });
});

describe('FAIRNESS_SECTION_ORDER', () => {
  it('lists tiers in severity order: dealbreaker, non-standard, fair', () => {
    expect(FAIRNESS_SECTION_ORDER).toEqual(['dealbreaker', 'non-standard', 'fair']);
  });
});
