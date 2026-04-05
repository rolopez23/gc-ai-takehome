import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

const mockPush = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: 'test-uuid' }),
}));

const SUCCESS_RESPONSE = {
  error: null,
  overall_fairness: 'fair',
  summary: 'All clauses are market standard.',
  call_to_action: [],
  clauses: [],
};

beforeEach(() => {
  mockPush.mockReset();
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(SUCCESS_RESPONSE), { status: 200 })),
  ));
});

describe('EvalResultContext', () => {
  test('stores and retrieves a result by UUID', async () => {
    const { useEvalResult, EvalResultProvider } = await import('@/app/evaluate-contract/eval-result-context');

    let storedResult: unknown;
    function TestHarness() {
      const { setResult, getResult } = useEvalResult();
      return (
        <button onClick={() => {
          setResult('abc', SUCCESS_RESPONSE);
          storedResult = getResult('abc');
        }}>Store</button>
      );
    }

    render(
      <EvalResultProvider>
        <TestHarness />
      </EvalResultProvider>,
    );

    await userEvent.click(screen.getByText('Store'));
    expect(storedResult).toEqual(SUCCESS_RESPONSE);
  });

  test('returns undefined for unknown UUID', async () => {
    const { useEvalResult, EvalResultProvider } = await import('@/app/evaluate-contract/eval-result-context');

    function TestHarness() {
      const { getResult } = useEvalResult();
      return <span data-testid="result">{String(getResult('nonexistent'))}</span>;
    }

    render(
      <EvalResultProvider>
        <TestHarness />
      </EvalResultProvider>,
    );

    expect(screen.getByTestId('result').textContent).toBe('undefined');
  });
});

describe('Navigate on success', () => {
  test('navigates to /contract/[uuid] on success', async () => {
    const { EvalResultProvider } = await import('@/app/evaluate-contract/eval-result-context');
    const EvaluateContractPage = (await import('@/app/evaluate-contract/page')).default;

    render(
      <EvalResultProvider>
        <EvaluateContractPage />
      </EvalResultProvider>,
    );

    const file = new File(['contract text'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.click(screen.getByRole('button', { name: /evaluate contract/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(expect.stringMatching(/\/contract\/.+/));
    });
  });

  test('UUID is a valid format', async () => {
    const { EvalResultProvider } = await import('@/app/evaluate-contract/eval-result-context');
    const EvaluateContractPage = (await import('@/app/evaluate-contract/page')).default;

    render(
      <EvalResultProvider>
        <EvaluateContractPage />
      </EvalResultProvider>,
    );

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

describe('Results page', () => {
  test('shows evaluation complete for valid result', async () => {
    const { EvalResultProvider, useEvalResult } = await import('@/app/evaluate-contract/eval-result-context');
    const ContractPage = (await import('@/app/contract/[id]/page')).default;

    function Wrapper() {
      const { setResult } = useEvalResult();
      setResult('test-uuid', SUCCESS_RESPONSE);
      return <ContractPage />;
    }

    render(
      <EvalResultProvider>
        <Wrapper />
      </EvalResultProvider>,
    );

    expect(screen.getByText(/evaluation complete/i)).toBeInTheDocument();
  });

  test('shows overall fairness value', async () => {
    const { EvalResultProvider, useEvalResult } = await import('@/app/evaluate-contract/eval-result-context');
    const ContractPage = (await import('@/app/contract/[id]/page')).default;

    function Wrapper() {
      const { setResult } = useEvalResult();
      setResult('test-uuid', SUCCESS_RESPONSE);
      return <ContractPage />;
    }

    render(
      <EvalResultProvider>
        <Wrapper />
      </EvalResultProvider>,
    );

    expect(screen.getByText('Fair')).toBeInTheDocument();
  });

  test('shows no evaluation found when result missing', async () => {
    const { EvalResultProvider } = await import('@/app/evaluate-contract/eval-result-context');
    const ContractPage = (await import('@/app/contract/[id]/page')).default;

    render(
      <EvalResultProvider>
        <ContractPage />
      </EvalResultProvider>,
    );

    expect(screen.getByText(/no evaluation found/i)).toBeInTheDocument();
  });
});
