import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import EvaluateContractPage from '@/app/evaluate-contract/page';

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

  it('logs SubmitPayload to console on submit', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    render(<EvaluateContractPage />);

    const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);

    await userEvent.type(
      screen.getByPlaceholderText(/instruction/i),
      'Focus on IP clauses',
    );

    await userEvent.click(screen.getByRole('button', { name: /evaluate/i }));

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        fileName: 'contract.pdf',
        fileType: '.pdf',
        instructions: 'Focus on IP clauses',
      }),
    );
    consoleSpy.mockRestore();
  });

  it('does not clear instructions when file is removed', async () => {
    render(<EvaluateContractPage />);

    await userEvent.type(
      screen.getByPlaceholderText(/instruction/i),
      'Check indemnification',
    );

    const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);
    await userEvent.click(screen.getByRole('button', { name: /remove/i }));

    expect(screen.getByPlaceholderText(/instruction/i)).toHaveValue(
      'Check indemnification',
    );
  });

  it('does not clear file when instructions are cleared', async () => {
    render(<EvaluateContractPage />);

    const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file);

    const textarea = screen.getByPlaceholderText(/instruction/i);
    await userEvent.type(textarea, 'Some text');
    await userEvent.clear(textarea);

    expect(screen.getByText('contract.pdf')).toBeInTheDocument();
  });
});
