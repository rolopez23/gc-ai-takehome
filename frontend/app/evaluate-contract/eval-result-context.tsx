'use client';

import { createContext, useContext, useRef, useMemo, type ReactNode } from 'react';
import type { EvalResponse } from './types';

interface EvalResultContextValue {
  setResult: (id: string, result: EvalResponse) => void;
  getResult: (id: string) => EvalResponse | undefined;
}

const EvalResultContext = createContext<EvalResultContextValue | null>(null);

export function EvalResultProvider({ children }: { children: ReactNode }) {
  const results = useRef(new Map<string, EvalResponse>());

  const value = useMemo<EvalResultContextValue>(() => ({
    setResult: (id, result) => results.current.set(id, result),
    getResult: (id) => results.current.get(id),
  }), []);

  return (
    <EvalResultContext value={value}>
      {children}
    </EvalResultContext>
  );
}

export function useEvalResult() {
  const ctx = useContext(EvalResultContext);
  if (!ctx) throw new Error('useEvalResult must be used within EvalResultProvider');
  return ctx;
}
