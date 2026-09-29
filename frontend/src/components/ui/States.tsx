import Link from "next/link";
import type { ReactNode } from "react";
import { Button } from "./Panel";
import { Icon } from "./Icon";

export function Skeleton({ className = "h-4 w-full" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-black/[0.05] ${className}`} />;
}

export function EmptyState({ title, body, action }: { title: string; body?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
      <div className="grid h-10 w-10 place-items-center rounded-full border border-line-2 text-muted">
        <Icon name="layers" />
      </div>
      <div className="font-display text-[15px] text-text">{title}</div>
      {body && <div className="max-w-sm text-[13px] text-muted">{body}</div>}
      {action}
    </div>
  );
}

export function RunFirstCta() {
  return (
    <Link href="/app/harmonize"
      className="inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-[13px] font-medium text-white hover:bg-[#0d9488]">
      <Icon name="play" className="h-3.5 w-3.5" /> Run harmonization
    </Link>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
      <div className="grid h-10 w-10 place-items-center rounded-full border border-bad/40 text-bad">
        <Icon name="alert" />
      </div>
      <div className="font-display text-[15px]">Could not load data</div>
      <div className="max-w-md text-[13px] text-muted">{message}</div>
      {onRetry && (
        <Button onClick={onRetry}>
          <Icon name="refresh" className="h-3.5 w-3.5" /> Retry
        </Button>
      )}
    </div>
  );
}
