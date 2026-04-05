import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import EvaluateContractPage from '@/app/evaluate-contract/page';

const ERROR_MESSAGE = /something went wrong/i;

beforeEach(() => {
  vi.restoreAllMocks();
});

async function stageFileAndSubmit(fetchMock: () => Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn(fetchMock));
  render(<EvaluateContractPage />);

  const file = new File(['contract text'], 'contract.txt', { type: 'text/plain' });
  await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
  await userEvent.click(screen.getByRole('button', { name: /evaluate contract/i }));
}

describe('Error display', () => {
  test('shows error on network failure', async () => {
    await stageFileAndSubmit(() => Promise.reject(new Error('network error')));

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });
  });

  test('shows error on non-200 response', async () => {
    await stageFileAndSubmit(() =>
      Promise.resolve(new Response(JSON.stringify({ error: 'server error' }), { status: 500 })),
    );

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });
  });

  test('shows error when Claude returns eval error', async () => {
    const evalError = { error: true, reason: 'This does not appear to be a contract.' };
    await stageFileAndSubmit(() =>
      Promise.resolve(new Response(JSON.stringify(evalError), { status: 200 })),
    );

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });
  });

  test('clears error when user retries', async () => {
    await stageFileAndSubmit(() => Promise.reject(new Error('network error')));

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });

    const successResponse = { error: null, overall_fairness: 'fair', summary: '', call_to_action: [], clauses: [] };
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify(successResponse), { status: 200 })),
    ));

    // File is preserved from the failed attempt — just retry
    await userEvent.click(screen.getByRole('button', { name: /evaluate contract/i }));

    await waitFor(() => {
      expect(screen.queryByText(ERROR_MESSAGE)).not.toBeInTheDocument();
    });
  });

  test('preserves file and instructions on error', async () => {
    await stageFileAndSubmit(() => Promise.reject(new Error('network error')));

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });

    expect(screen.getByText('contract.txt')).toBeInTheDocument();
  });
});
