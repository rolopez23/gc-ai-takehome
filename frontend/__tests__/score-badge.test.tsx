import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ScoreBadge from '@/app/contract/[id]/ScoreBadge';
import { COLORS } from '@/app/evaluate-contract/fairness-utils';

describe('ScoreBadge', () => {
  it('renders Dealbreaker with fail styling for dealbreaker', () => {
    render(<ScoreBadge rating="dealbreaker" />);
    const badge = screen.getByText('Dealbreaker');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain(COLORS.fail);
  });

  it('renders Non-Standard with warning styling for non-standard', () => {
    render(<ScoreBadge rating="non-standard" />);
    const badge = screen.getByText('Non-Standard');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain(COLORS.warning);
  });

  it('renders Standard with pass styling for fair', () => {
    render(<ScoreBadge rating="fair" />);
    const badge = screen.getByText('Standard');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain(COLORS.pass);
  });
});
