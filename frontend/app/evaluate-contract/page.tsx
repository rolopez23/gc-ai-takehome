'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropZone } from './FileDropZone';
import { UploadResponseSchema, ReviewResponseSchema } from './types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const POLL_INTERVAL = 2000;
const POLL_TIMEOUT = 10 * 60 * 1000;

const STATUS_TEXT: Record<string, string> = {
  pending: 'Preparing evaluation...',
  reading: 'Reading document...',
  evaluating: 'Evaluating contract...',
};

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

const HEIGHT = { '3.5': 'h-3.5', '4': 'h-4', '5': 'h-5', '8': 'h-8' } as const;
const WIDTH = { '14': 'w-14', '20': 'w-20', '28': 'w-28', '32': 'w-32', '2/3': 'w-2/3', '3/4': 'w-3/4', '4/5': 'w-4/5', '5/6': 'w-5/6', 'full': 'w-full' } as const;

function ShimmerBar({ h, w, pill }: { h: keyof typeof HEIGHT; w: keyof typeof WIDTH; pill?: boolean }) {
  return (
    <div className={`animate-pulse bg-foreground/[0.06] ${HEIGHT[h]} ${WIDTH[w]} ${pill ? 'rounded-full' : 'rounded'}`} />
  );
}

function LoadingShimmer({ statusText }: { statusText: string }) {
  return (
    <div data-testid="loading-shimmer" className="space-y-6" role="status">
      <p className="sr-only">Evaluating contract, please wait...</p>
      <p className="text-sm text-foreground/60" data-testid="status-text">{statusText}</p>
      <div className="space-y-3">
        <ShimmerBar h="8" w="28" pill />
        <ShimmerBar h="4" w="full" />
        <ShimmerBar h="4" w="4/5" />
      </div>

      <div className="space-y-2 border-l-2 border-foreground/[0.06] pl-4">
        <ShimmerBar h="3.5" w="3/4" />
        <ShimmerBar h="3.5" w="2/3" />
      </div>

      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="space-y-2.5 rounded-lg border border-foreground/[0.06] p-4"
        >
          <div className="flex items-center gap-3">
            <ShimmerBar h="5" w="14" />
            <ShimmerBar h="5" w="32" />
            <div className="ml-auto">
              <ShimmerBar h="5" w="20" pill />
            </div>
          </div>
          <ShimmerBar h="3.5" w="full" />
          <ShimmerBar h="3.5" w="5/6" />
        </div>
      ))}
    </div>
  );
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
        setError(result.failure_message);
        setIsLoading(false);
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      setError(e instanceof Error ? e.message : 'Something went wrong');
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-12" aria-busy={isLoading}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluate Contract</h1>

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
        className="rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background disabled:opacity-40"
      >
        Evaluate Contract
      </button>

      {error && !isLoading && (
        <p className="text-sm text-red-500" role="alert">{error}</p>
      )}
    </div>
  );
}
