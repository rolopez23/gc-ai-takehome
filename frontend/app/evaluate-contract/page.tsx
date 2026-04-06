'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropZone } from '@/app/evaluate-contract/FileDropZone';
import { LoadingShimmer } from '@/app/evaluate-contract/LoadingShimmer';
import { BACKEND_URL, POLL_INTERVAL, POLL_TIMEOUT, STATUS_TEXT } from '@/app/evaluate-contract/constants';
import { UploadResponseSchema, ReviewResponseSchema } from '@/app/evaluate-contract/types';
import { getFailureMessage } from '@/app/evaluate-contract/failure-messages';

const ERROR_ALERT = 'flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg';

async function uploadContract(file: File, instructions: string, signal: AbortSignal) {
  const form = new FormData();
  form.append('file', file);
  if (instructions.trim()) form.append('instructions', instructions);
  const res = await fetch(`${BACKEND_URL}/api/contracts/upload`, {
    method: 'POST',
    body: form,
    signal,
  });
  if (!res.ok) {
    if (res.status === 413) throw new Error('File too large (max 10MB)');
    if (res.status === 400) {
      const data = await res.json();
      throw new Error(data.detail || 'Invalid file');
    }
    throw new Error('Upload failed');
  }
  return UploadResponseSchema.parse(await res.json());
}

async function pollReview(reviewId: string, signal: AbortSignal, onStatus?: (s: string) => void) {
  const start = Date.now();
  while (Date.now() - start < POLL_TIMEOUT) {
    const res = await fetch(`${BACKEND_URL}/api/reviews/${reviewId}`, { signal });
    if (!res.ok) throw new Error('Failed to check review status');
    const data = ReviewResponseSchema.parse(await res.json());
    if (data.status === 'completed' || data.status === 'failed') return data;
    onStatus?.(data.status);
    await new Promise((r) => setTimeout(r, POLL_INTERVAL));
  }
  throw new Error('Evaluation timed out — please try again');
}

export default function EvaluateContractPage() {
  const [file, setFile] = useState<File | null>(null);
  const [instructions, setInstructions] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusText, setStatusText] = useState('Preparing evaluation...');
  const router = useRouter();
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  async function handleSubmit() {
    if (!file) return;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setError(null);
    setIsLoading(true);
    setStatusText('Preparing evaluation...');
    try {
      const { contract_id, review_id } = await uploadContract(file, instructions, controller.signal);
      const result = await pollReview(review_id, controller.signal, (s) =>
        setStatusText(STATUS_TEXT[s] || 'Processing...'),
      );
      if (result.status === 'completed') {
        router.push(`/contract/${contract_id}`);
      } else {
        setError(getFailureMessage(result.failure_code));
        setIsLoading(false);
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      setError(e instanceof Error ? e.message : 'Something went wrong');
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-6 pt-12" aria-busy={isLoading}>
      <h1 className="text-2xl font-bold tracking-tight">Evaluate Contract</h1>

      {isLoading ? (
        <LoadingShimmer statusText={statusText} />
      ) : (
        <>
          <FileDropZone file={file} onFileChange={setFile} />

          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Add any specific instructions for the evaluation..."
            rows={4}
            className="w-full rounded-lg border border-foreground/20 bg-transparent px-4 py-3 text-sm placeholder:text-foreground/40 focus:border-foreground/40 focus:outline-none"
          />
        </>
      )}

      <button
        type="button"
        disabled={!file || isLoading}
        onClick={handleSubmit}
        className="w-full sm:w-auto rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background disabled:opacity-40"
      >
        Evaluate Contract
      </button>

      {error && !isLoading && (
        <div className={ERROR_ALERT} role="alert">
          <span>⚠</span>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
