import Link from 'next/link';

export function Nav() {
  return (
    <nav className="border-b border-border">
      <div className="mx-auto flex h-14 max-w-2xl items-center justify-between px-6">
        <Link href="/" className="text-sm font-semibold tracking-tight">
          ◆ ContractAI
        </Link>
        <Link
          href="/evaluate-contract"
          className="text-sm text-muted hover:text-foreground transition-colors"
        >
          Evaluate Contract
        </Link>
      </div>
    </nav>
  );
}
