import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ClauseCard from '@/app/contract/[id]/ClauseCard';
import ClauseSection from '@/app/contract/[id]/ClauseSection';
import type { EvalClause } from '@/app/evaluate-contract/types';

const TEST_CLAUSE: EvalClause = {
  section_number: '3.1',
  clause_type: 'Liability Cap',
  purpose: 'Limits financial exposure',
  fairness: 'dealbreaker',
  market_standard: 'Typically 12 months of fees',
  explanation: 'Unlimited liability is unacceptable',
};

const TEST_CLAUSE_2: EvalClause = {
  section_number: '5.2',
  clause_type: 'Payment Terms',
  purpose: 'Defines payment schedule',
  fairness: 'dealbreaker',
  market_standard: 'Net 30',
  explanation: 'Net 15 is aggressive but negotiable',
};

describe('ClauseCard', () => {
  it('renders section_number, clause_type, and explanation', () => {
    render(<ClauseCard clause={TEST_CLAUSE} />);
    expect(screen.getByText('3.1')).toBeInTheDocument();
    expect(screen.getByText('Liability Cap')).toBeInTheDocument();
    expect(screen.getByText('Unlimited liability is unacceptable')).toBeInTheDocument();
  });
});

describe('ClauseSection', () => {
  it('renders header with label and count', () => {
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE, TEST_CLAUSE_2]} />);
    expect(screen.getByText(/Egregious/)).toBeInTheDocument();
    expect(screen.getByText(/\(2\)/)).toBeInTheDocument();
  });

  it('starts collapsed — clauses not visible', () => {
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE]} />);
    expect(screen.queryByText('Unlimited liability is unacceptable')).not.toBeInTheDocument();
  });

  it('clicking header expands section and shows clauses', async () => {
    const user = userEvent.setup();
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE, TEST_CLAUSE_2]} />);
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Unlimited liability is unacceptable')).toBeInTheDocument();
    expect(screen.getByText('Net 15 is aggressive but negotiable')).toBeInTheDocument();
  });

  it('clicking header again collapses section', async () => {
    const user = userEvent.setup();
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE]} />);
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Unlimited liability is unacceptable')).toBeInTheDocument();
    await user.click(screen.getByRole('button'));
    expect(screen.queryByText('Unlimited liability is unacceptable')).not.toBeInTheDocument();
  });

  it('renders celebratory placeholder for empty egregious section', () => {
    render(<ClauseSection rating="dealbreaker" clauses={[]} />);
    expect(screen.getByText(/No egregious clauses/)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders celebratory placeholder for empty unfair section', () => {
    render(<ClauseSection rating="non-standard" clauses={[]} />);
    expect(screen.getByText(/No unfair clauses/)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('expanded section has scroll constraint', async () => {
    const user = userEvent.setup();
    render(<ClauseSection rating="dealbreaker" clauses={[TEST_CLAUSE]} />);
    await user.click(screen.getByRole('button'));
    const clauseList = screen.getByText('Unlimited liability is unacceptable').closest('[class*="max-h-"]');
    expect(clauseList).not.toBeNull();
    expect(clauseList!.className).toContain('overflow-y-auto');
  });
});
