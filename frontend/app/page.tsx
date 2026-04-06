'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BACKEND_URL, STATUS_TEXT } from '@/app/evaluate-contract/constants';
import { ContractListItemSchema, type ContractListItem } from '@/app/contract-list-types';
import { z } from 'zod';
import ScoreBadge from '@/app/contract/[id]/ScoreBadge';

function timeAgo(dateStr: string) {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function Home() {
  const [contracts, setContracts] = useState<ContractListItem[] | null>(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/contracts/`)
      .then((res) => res.json())
      .then((data) => {
        const parsed = z.array(ContractListItemSchema).safeParse(data);
        setContracts(parsed.success ? parsed.data : []);
      })
      .catch(() => setContracts([]));
  }, []);

  if (contracts === null) {
    return null;
  }

  if (contracts.length === 0) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <span className="text-2xl text-muted">◆</span>
        <h1 className="mt-4 text-2xl font-bold">Evaluate your first contract</h1>
        <p className="mt-2 max-w-sm text-sm text-muted">
          Upload a contract to get an AI-powered fairness analysis.
        </p>
        <Link
          href="/evaluate-contract"
          className="mt-6 rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background"
        >
          Get Started
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 pt-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Your Contracts</h1>
        <Link
          href="/evaluate-contract"
          className="rounded-lg bg-foreground px-4 py-2 text-sm font-medium text-background"
        >
          Evaluate Contract
        </Link>
      </div>
      <div className="mt-6 space-y-3">
        {contracts.map((contract) => (
          <Link
            key={contract.id}
            href={`/contract/${contract.id}`}
            className="block rounded-lg border border-border bg-surface p-4 transition-colors hover:bg-foreground/[0.03]"
          >
            <div className="truncate font-medium">{contract.name}</div>
            <div className="mt-1 flex items-center gap-2 text-sm">
              <StatusDisplay contract={contract} />
              <span className="ml-auto text-xs text-muted">{timeAgo(contract.created_at)}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function StatusDisplay({ contract }: { contract: ContractListItem }) {
  if (contract.failure_code) {
    return <span className="text-egregious-fg">Failed</span>;
  }

  if (
    contract.review_status === 'completed' &&
    contract.overall_fairness
  ) {
    return <ScoreBadge rating={contract.overall_fairness} />;
  }

  if (contract.review_status && contract.review_status in STATUS_TEXT) {
    return <span className="text-muted">{STATUS_TEXT[contract.review_status]}</span>;
  }

  return null;
}
