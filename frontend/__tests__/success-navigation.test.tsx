import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

const mockPush = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: 'test-uuid' }),
}));

const CONTRACT_ID = 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d';
const REVIEW_ID = 'f6e5d4c3-b2a1-4f9e-8d7c-6b5a4c3d2e1f';

const UPLOAD_RESPONSE = {
  contract_id: CONTRACT_ID,
  review_id: REVIEW_ID,
  status: 'pending',
};

const REVIEW_COMPLETED = {
  id: REVIEW_ID,
  contract_id: CONTRACT_ID,
  status: 'completed',
  overall_fairness: 'fair',
  summary: 'All clauses are market standard.',
  call_to_action: [],
  clauses: [],
  completed_at: '2026-01-01T00:00:00Z',
};

let mockFetch: ReturnType<typeof vi.fn>;

beforeEach(() => {
  mockFetch = vi.fn();
  vi.stubGlobal('fetch', mockFetch);
  mockPush.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Navigate on success', () => {
  test('navigates to /contract/[uuid] on success', async () => {
    mockFetch
      .mockResolvedValueOnce(new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(REVIEW_COMPLETED), { status: 200 }));

    const EvaluateContractPage = (await import('@/app/evaluate-contract/page')).default;
    render(<EvaluateContractPage />);

    const file = new File(['contract text'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.click(screen.getByRole('button', { name: /evaluate contract/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(expect.stringMatching(/\/contract\/.+/));
    });
  });

  test('UUID is a valid format', async () => {
    mockFetch
      .mockResolvedValueOnce(new Response(JSON.stringify(UPLOAD_RESPONSE), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(REVIEW_COMPLETED), { status: 200 }));

    const EvaluateContractPage = (await import('@/app/evaluate-contract/page')).default;
    render(<EvaluateContractPage />);

    const file = new File(['contract text'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.click(screen.getByRole('button', { name: /evaluate contract/i }));

    await waitFor(() => {
      const path = mockPush.mock.calls[0][0] as string;
      const uuid = path.replace('/contract/', '');
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    });
  });
});

describe('Results page via backend', () => {
  test('shows evaluation complete for valid result', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(REVIEW_COMPLETED),
    });

    const ContractPage = (await import('@/app/contract/[id]/page')).default;
    render(<ContractPage />);

    await waitFor(() => {
      expect(screen.getByText(/evaluation complete/i)).toBeInTheDocument();
    });
  });

  test('shows overall fairness value', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(REVIEW_COMPLETED),
    });

    const ContractPage = (await import('@/app/contract/[id]/page')).default;
    render(<ContractPage />);

    await waitFor(() => {
      expect(screen.getByText('Standard')).toBeInTheDocument();
    });
  });

  test('shows no evaluation found on 404', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({}),
    });

    const ContractPage = (await import('@/app/contract/[id]/page')).default;
    render(<ContractPage />);

    await waitFor(() => {
      expect(screen.getByText(/no evaluation found/i)).toBeInTheDocument();
    });
  });
});
