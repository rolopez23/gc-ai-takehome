import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import EvaluateContractPage from '@/app/evaluate-contract/page';

const VALID_RESPONSE = {
  error: null,
  overall_fairness: 'fair',
  summary: '',
  call_to_action: [],
  clauses: [],
};

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(VALID_RESPONSE), { status: 200 }))),
  );
});

describe('EvaluateContractPage', () => {
  it('renders the page heading', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByRole('heading', { name: /evaluate/i })).toBeInTheDocument();
  });

  it('renders the file drop zone', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
  });

  it('renders the instructions textarea', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByPlaceholderText(/instruction/i)).toBeInTheDocument();
  });

  it('renders the submit button', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByRole('button', { name: /evaluate/i })).toBeInTheDocument();
  });

  it('disables submit button when no file is staged', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByRole('button', { name: /evaluate/i })).toBeDisabled();
  });

  it('calls /api/evaluate on submit', async () => {
    render(<EvaluateContractPage />);

    const file = new File(['content'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.click(screen.getByRole('button', { name: /evaluate/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/evaluate', expect.objectContaining({
        method: 'POST',
      }));
    });
  });

  it('does not clear instructions when file is removed', async () => {
    render(<EvaluateContractPage />);

    await userEvent.type(
      screen.getByPlaceholderText(/instruction/i),
      'Check indemnification',
    );

    const file = new File(['content'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.click(screen.getByRole('button', { name: /remove/i }));

    expect(screen.getByPlaceholderText(/instruction/i)).toHaveValue(
      'Check indemnification',
    );
  });

  it('does not clear file when instructions are cleared', async () => {
    render(<EvaluateContractPage />);

    const file = new File(['content'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);

    const textarea = screen.getByPlaceholderText(/instruction/i);
    await userEvent.type(textarea, 'Some text');
    await userEvent.clear(textarea);

    expect(screen.getByText('contract.txt')).toBeInTheDocument();
  });

  it('clears file and instructions after submit', async () => {
    render(<EvaluateContractPage />);

    const file = new File(['content'], 'contract.txt', { type: 'text/plain' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.type(
      screen.getByPlaceholderText(/instruction/i),
      'Focus on IP clauses',
    );

    await userEvent.click(screen.getByRole('button', { name: /evaluate/i }));

    await waitFor(() => {
      expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText(/instruction/i)).toHaveValue('');
    expect(screen.getByRole('button', { name: /evaluate/i })).toBeDisabled();
  });
});
