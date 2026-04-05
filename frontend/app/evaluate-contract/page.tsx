'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropZone } from './FileDropZone';
import { EvalErrorSchema, EvalSuccessSchema, type EvalSuccess } from './types';
import { useEvalResult } from './eval-result-context';

async function evaluateContract(file: File, instructions: string): Promise<EvalSuccess> {
  const text = await file.text();
  const res = await fetch('/api/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, instructions }),
  });
  if (!res.ok) throw new Error('evaluation failed');
  const data = await res.json();
  if (EvalErrorSchema.safeParse(data).success) throw new Error('eval error');
  const parsed = EvalSuccessSchema.safeParse(data);
  if (!parsed.success) throw new Error('unexpected response shape');
  return parsed.data;
}

const HEIGHT = { '3.5': 'h-3.5', '4': 'h-4', '5': 'h-5', '8': 'h-8' } as const;
const WIDTH = { '14': 'w-14', '20': 'w-20', '28': 'w-28', '32': 'w-32', '2/3': 'w-2/3', '3/4': 'w-3/4', '4/5': 'w-4/5', '5/6': 'w-5/6', 'full': 'w-full' } as const;

function ShimmerBar({ h, w, pill }: { h: keyof typeof HEIGHT; w: keyof typeof WIDTH; pill?: boolean }) {
  return (
    <div className={`animate-pulse bg-foreground/[0.06] ${HEIGHT[h]} ${WIDTH[w]} ${pill ? 'rounded-full' : 'rounded'}`} />
  );
}

function LoadingShimmer() {
  return (
    <div data-testid="loading-shimmer" className="space-y-6" role="status">
      <p className="sr-only">Evaluating contract, please wait...</p>
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
  const router = useRouter();
  const { setResult } = useEvalResult();

  async function handleSubmit() {
    if (!file) return;
    setError(null);
    setIsLoading(true);
    try {
      const result = await evaluateContract(file, instructions);
      const id = crypto.randomUUID();
      setResult(id, result);
      router.push(`/contract/${id}`);
    } catch {
      setError('Something went wrong. Try again.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-12" aria-busy={isLoading}>
      <h1 className="text-3xl font-bold tracking-tight">Evaluate Contract</h1>

      {isLoading ? (
        <LoadingShimmer />
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
