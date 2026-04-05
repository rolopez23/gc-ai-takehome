import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ClauseCard from '@/app/contract/[id]/ClauseCard';
import type { EvalClause } from '@/app/evaluate-contract/types';

const TEST_CLAUSE: EvalClause = {
  section_number: '3.1',
  clause_type: 'Liability Cap',
  purpose: 'Limits financial exposure',
  fairness: 'dealbreaker',
  market_standard: 'Typically 12 months of fees',
  explanation: 'Unlimited liability is unacceptable',
};

describe('ClauseCard', () => {
  it('renders section_number, clause_type, and explanation', () => {
    render(<ClauseCard clause={TEST_CLAUSE} />);
    expect(screen.getByText('3.1')).toBeInTheDocument();
    expect(screen.getByText('Liability Cap')).toBeInTheDocument();
    expect(screen.getByText('Unlimited liability is unacceptable')).toBeInTheDocument();
  });
});
