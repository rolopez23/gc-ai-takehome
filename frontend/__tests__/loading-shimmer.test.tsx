import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import EvaluateContractPage from '@/app/evaluate-contract/page';
import { EvalResultProvider } from '@/app/evaluate-contract/eval-result-context';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

let fetchResolver: (res: Response) => void;

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => {
      return new Promise((resolve) => {
        fetchResolver = resolve;
      });
    }),
  );
});

async function stageFileAndSubmit() {
  render(<EvalResultProvider><EvaluateContractPage /></EvalResultProvider>);

  const file = new File(['contract text'], 'contract.txt', { type: 'text/plain' });
  await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
  await userEvent.click(screen.getByRole('button', { name: /evaluate contract/i }));
}

const VALID_RESPONSE = { error: null, overall_fairness: 'fair', summary: '', call_to_action: [], clauses: [] };

function resolveFetch() {
  fetchResolver(new Response(JSON.stringify(VALID_RESPONSE), { status: 200 }));
}

describe('Loading shimmer', () => {
  test('shows shimmer when submitting', async () => {
    await stageFileAndSubmit();
    expect(screen.getByTestId('loading-shimmer')).toBeInTheDocument();
  });

  test('disables button when submitting', async () => {
    await stageFileAndSubmit();
    expect(screen.getByRole('button', { name: /evaluate contract/i })).toBeDisabled();
  });

  test('keeps shimmer on success until navigation', async () => {
    await stageFileAndSubmit();
    expect(screen.getByTestId('loading-shimmer')).toBeInTheDocument();

    resolveFetch();

    await waitFor(() => {
      expect(screen.getByTestId('loading-shimmer')).toBeInTheDocument();
    });
  });

  test('hides shimmer on error', async () => {
    await stageFileAndSubmit();
    expect(screen.getByTestId('loading-shimmer')).toBeInTheDocument();

    fetchResolver(new Response(JSON.stringify({ error: true, reason: 'fail' }), { status: 200 }));

    await waitFor(() => {
      expect(screen.queryByTestId('loading-shimmer')).not.toBeInTheDocument();
    });
  });

  test('sends file text to /api/evaluate', async () => {
    await stageFileAndSubmit();
    resolveFetch();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/evaluate', expect.objectContaining({
        method: 'POST',
      }));
    });
  });
});
