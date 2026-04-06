const HEIGHT = { '3.5': 'h-3.5', '4': 'h-4', '5': 'h-5', '8': 'h-8' } as const;
const WIDTH = { '14': 'w-14', '20': 'w-20', '28': 'w-28', '32': 'w-32', '2/3': 'w-2/3', '3/4': 'w-3/4', '4/5': 'w-4/5', '5/6': 'w-5/6', 'full': 'w-full' } as const;

function ShimmerBar({ h, w, pill }: { h: keyof typeof HEIGHT; w: keyof typeof WIDTH; pill?: boolean }) {
  return (
    <div className={`animate-pulse bg-foreground/[0.04] ${HEIGHT[h]} ${WIDTH[w]} ${pill ? 'rounded-full' : 'rounded'}`} />
  );
}

export function LoadingShimmer({ statusText }: { statusText: string }) {
  return (
    <div data-testid="loading-shimmer" className="space-y-6" role="status">
      <div className="opacity-0 animate-[fadeIn_300ms_ease-out_forwards]">
        <p className="sr-only">Evaluating contract, please wait...</p>
        <p className="text-sm text-foreground/60" data-testid="status-text">{statusText}</p>
        <div className="mt-6 space-y-3">
          <ShimmerBar h="8" w="28" pill />
          <ShimmerBar h="4" w="full" />
          <ShimmerBar h="4" w="4/5" />
        </div>

        <div className="mt-6 space-y-2 border-l-2 border-foreground/[0.06] pl-4">
          <ShimmerBar h="3.5" w="3/4" />
          <ShimmerBar h="3.5" w="2/3" />
        </div>

        {[0, 1, 2].map((i) => (
          <div
            key={i}
            data-testid="shimmer-card"
            style={{ animationDelay: `${i * 150}ms` }}
            className="mt-6 space-y-2.5 rounded-lg border border-foreground/[0.06] p-4"
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
    </div>
  );
}
