import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

const uuid = '550e8400-e29b-41d4-a716-446655440000';
const uuid2 = '660e8400-e29b-41d4-a716-446655440001';

const mockFetch = vi.fn();

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function mockFetchResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  });
}

// --- Cycle 1: Zod schema tests ---

describe('ContractListItemSchema', () => {
  it('parses valid contract list item', async () => {
    const { ContractListItemSchema } = await import('@/app/contract-list-types');
    const data = {
      id: uuid,
      name: 'lease_agreement.pdf',
      upload_type: 'application/pdf',
      created_at: '2026-04-05T12:00:00Z',
      review_status: 'completed',
      overall_fairness: 'fair',
      failure_code: null,
    };
    const result = ContractListItemSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.name).toBe('lease_agreement.pdf');
      expect(result.data.overall_fairness).toBe('fair');
      expect(result.data.failure_code).toBeNull();
    }
  });

  it('parses item with all nullable fields null', async () => {
    const { ContractListItemSchema } = await import('@/app/contract-list-types');
    const data = {
      id: uuid,
      name: 'contract.pdf',
      upload_type: 'application/pdf',
      created_at: '2026-04-05T12:00:00Z',
      review_status: null,
      overall_fairness: null,
      failure_code: null,
    };
    const result = ContractListItemSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('rejects item missing id', async () => {
    const { ContractListItemSchema } = await import('@/app/contract-list-types');
    const data = {
      name: 'contract.pdf',
      upload_type: 'application/pdf',
      created_at: '2026-04-05T12:00:00Z',
      review_status: null,
      overall_fairness: null,
      failure_code: null,
    };
    const result = ContractListItemSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});

// --- Cycle 2: Empty state tests ---

describe('Dashboard empty state', () => {
  beforeEach(() => {
    vi.resetModules();
    mockFetch.mockReset();
    vi.stubGlobal('fetch', mockFetch);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows empty state CTA when no contracts', async () => {
    mockFetch.mockReturnValue(mockFetchResponse([]));
    const { default: Home } = await import('@/app/page');
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('Evaluate your first contract')).toBeInTheDocument();
    });
    const link = screen.getByRole('link', { name: /get started/i });
    expect(link).toHaveAttribute('href', '/evaluate-contract');
  });

  it('shows subtext in empty state', async () => {
    mockFetch.mockReturnValue(mockFetchResponse([]));
    const { default: Home } = await import('@/app/page');
    render(<Home />);
    await waitFor(() => {
      expect(
        screen.getByText('Upload a contract to get an AI-powered fairness analysis.'),
      ).toBeInTheDocument();
    });
  });
});
