import Link from "next/link";

const NAV = "border-b border-border";
const NAV_INNER =
  "mx-auto flex h-14 max-w-2xl items-center justify-between px-6";
const LOGO = "text-sm font-semibold tracking-tight";
const NAV_LINK = "text-sm text-muted hover:text-foreground transition-colors";

export function Nav() {
  return (
    <nav className={NAV}>
      <div className={NAV_INNER}>
        <Link href="/" className={LOGO}>
          Your Contracts
        </Link>
        <Link href="/evaluate-contract" className={NAV_LINK}>
          Evaluate Contract
        </Link>
      </div>
    </nav>
  );
}
