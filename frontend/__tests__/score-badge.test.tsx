import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ScoreBadge from '@/app/contract/[id]/ScoreBadge';

describe('ScoreBadge', () => {
  it('renders Egregious with red styling for dealbreaker', () => {
    render(<ScoreBadge rating="dealbreaker" />);
    const badge = screen.getByText('Egregious');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('text-red-600');
  });

  it('renders Unfair with yellow styling for non-standard', () => {
    render(<ScoreBadge rating="non-standard" />);
    const badge = screen.getByText('Unfair');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('text-yellow-600');
  });

  it('renders Fair with green styling for fair', () => {
    render(<ScoreBadge rating="fair" />);
    const badge = screen.getByText('Fair');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('text-green-600');
  });
});
