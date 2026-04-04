import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { FileDropZone } from '@/app/evaluate-contract/FileDropZone';

describe('FileDropZone', () => {
  it('renders the drop zone with drag and drop prompt', () => {
    render(<FileDropZone onFileChange={vi.fn()} />);
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
  });

  it('renders a browse button', () => {
    render(<FileDropZone onFileChange={vi.fn()} />);
    expect(screen.getByText(/browse/i)).toBeInTheDocument();
  });

  it('has a hidden file input with correct accept types', () => {
    render(<FileDropZone onFileChange={vi.fn()} />);
    const input = screen.getByLabelText<HTMLInputElement>(/upload contract file/i);
    expect(input).toBeInTheDocument();
    expect(input.accept).toBe('.pdf,.txt,.doc,.docx');
  });

  it('stages a valid file and calls onFileChange', async () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/upload contract file/i);
    await userEvent.upload(input, file);

    expect(onFileChange).toHaveBeenCalledWith(file);
    expect(screen.getByText('contract.pdf')).toBeInTheDocument();
  });

  it('shows error for invalid file extension', () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const file = new File(['content'], 'image.png', { type: 'image/png' });
    const input = screen.getByLabelText(/upload contract file/i);
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/file type not allowed/i)).toBeInTheDocument();
    expect(onFileChange).not.toHaveBeenCalled();
  });

  it('shows error for oversized file', () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const bigContent = new ArrayBuffer(6 * 1024 * 1024);
    const file = new File([bigContent], 'big.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/upload contract file/i);
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/5 MB/i)).toBeInTheDocument();
    expect(onFileChange).not.toHaveBeenCalled();
  });

  it('removes staged file when remove button is clicked', async () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/upload contract file/i);
    await userEvent.upload(input, file);
    expect(screen.getByText('contract.pdf')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /remove/i }));
    expect(screen.queryByText('contract.pdf')).not.toBeInTheDocument();
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
    expect(onFileChange).toHaveBeenLastCalledWith(null);
  });

  it('replaces staged file when a new file is selected', async () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const file1 = new File(['a'], 'first.pdf', { type: 'application/pdf' });
    const file2 = new File(['b'], 'second.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    const input = screen.getByLabelText(/upload contract file/i);

    await userEvent.upload(input, file1);
    expect(screen.getByText('first.pdf')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /remove/i }));
    await userEvent.upload(screen.getByLabelText(/upload contract file/i), file2);

    expect(screen.queryByText('first.pdf')).not.toBeInTheDocument();
    expect(screen.getByText('second.docx')).toBeInTheDocument();
  });

  it('accepts a valid file via drag and drop', () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const dropZone = screen.getByText(/drag.+drop/i).closest('div')!;
    const file = new File(['content'], 'contract.txt', { type: 'text/plain' });

    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

    expect(onFileChange).toHaveBeenCalledWith(file);
    expect(screen.getByText('contract.txt')).toBeInTheDocument();
  });

  it('rejects an invalid file via drag and drop', () => {
    const onFileChange = vi.fn();
    render(<FileDropZone onFileChange={onFileChange} />);

    const dropZone = screen.getByText(/drag.+drop/i).closest('div')!;
    const file = new File(['content'], 'image.jpg', { type: 'image/jpeg' });

    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

    expect(screen.getByText(/file type not allowed/i)).toBeInTheDocument();
    expect(onFileChange).not.toHaveBeenCalled();
  });
});
