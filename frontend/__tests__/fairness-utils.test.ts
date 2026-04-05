import { describe, it, expect } from 'vitest';
import { getFairnessDisplay } from '@/app/evaluate-contract/fairness-utils';

describe('getFairnessDisplay', () => {
  it('maps dealbreaker to Egregious', () => {
    const display = getFairnessDisplay('dealbreaker');
    expect(display.label).toBe('Egregious');
  });

  it('maps non-standard to Unfair', () => {
    const display = getFairnessDisplay('non-standard');
    expect(display.label).toBe('Unfair');
  });

  it('maps fair to Fair', () => {
    const display = getFairnessDisplay('fair');
    expect(display.label).toBe('Fair');
  });
});
