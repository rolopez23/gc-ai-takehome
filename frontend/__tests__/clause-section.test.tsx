import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
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
});
