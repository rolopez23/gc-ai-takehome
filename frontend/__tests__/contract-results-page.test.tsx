import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import type { EvalSuccess } from '@/app/evaluate-contract/types';

const mockGetResult = vi.fn();

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-uuid' }),
}));

vi.mock('@/app/evaluate-contract/eval-result-context', () => ({
  useEvalResult: () => ({ getResult: mockGetResult }),
}));

const SUCCESS_RESULT: EvalSuccess = {
  error: null,
  overall_fairness: 'dealbreaker',
  summary: '1 dealbreaker, 2 negotiating points, 4 acceptable clauses',
  call_to_action: ['Fix the liability cap'],
  clauses: [
    {
      section_number: '3.1',
      clause_type: 'Liability Cap',
      purpose: 'Limits financial exposure',
      fairness: 'dealbreaker',
      market_standard: 'Typically 12 months of fees',
      explanation: 'Unlimited liability is unacceptable',
    },
    {
      section_number: '5.2',
      clause_type: 'Payment Terms',
      purpose: 'Defines payment schedule',
      fairness: 'non-standard',
      market_standard: 'Net 30',
      explanation: 'Net 15 is aggressive but negotiable',
    },
    {
      section_number: '7.1',
      clause_type: 'Term',
      purpose: 'Contract duration',
      fairness: 'fair',
      market_standard: '12-month auto-renew',
      explanation: 'Standard 12-month term with 30-day notice',
    },
  ],
};

describe('ContractPage', () => {
  beforeEach(() => {
    vi.resetModules();
    mockGetResult.mockReset();
  });

  it('renders score badge with correct label', async () => {
    mockGetResult.mockReturnValue(SUCCESS_RESULT);
    const { default: ContractPage } = await import('@/app/contract/[id]/page');
    render(<ContractPage />);
    expect(screen.getByText('Egregious')).toBeInTheDocument();
  });

  it('renders summary text', async () => {
    mockGetResult.mockReturnValue(SUCCESS_RESULT);
    const { default: ContractPage } = await import('@/app/contract/[id]/page');
    render(<ContractPage />);
    expect(screen.getByText(SUCCESS_RESULT.summary)).toBeInTheDocument();
  });

  it('renders link back to evaluate page', async () => {
    mockGetResult.mockReturnValue(SUCCESS_RESULT);
    const { default: ContractPage } = await import('@/app/contract/[id]/page');
    render(<ContractPage />);
    const link = screen.getByRole('link', { name: /evaluate/i });
    expect(link).toHaveAttribute('href', '/evaluate-contract');
  });

  it('renders fallback when no result found', async () => {
    mockGetResult.mockReturnValue(undefined);
    const { default: ContractPage } = await import('@/app/contract/[id]/page');
    render(<ContractPage />);
    expect(screen.getByText('No evaluation found')).toBeInTheDocument();
  });
});
