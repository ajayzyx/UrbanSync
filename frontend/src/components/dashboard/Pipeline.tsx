import clsx from "clsx";
import type { Stage } from "@/lib/types";
import { Icon } from "../ui/Icon";

function duration(s: Stage): string | null {
  if (!s.started_at || !s.finished_at) return null;
  const ms = new Date(s.finished_at).getTime() - new Date(s.started_at).getTime();
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

const PLACEHOLDER: Stage[] = [
  ["ingest", "Ingest"], ["normalize", "Normalize CRS"], ["match", "Spatial match"], ["attributes", "Map attributes"],
  ["validate", "Validate topology"], ["resolve", "Detect conflicts"], ["harmonize", "Harmonize"],
].map(([key, label]) => ({ key, label, status: "pending", started_at: null, finished_at: null, detail: null }));

export function Pipeline({ stages, compact = false }: { stages?: Stage[]; compact?: boolean }) {
  const list = stages?.length ? stages : PLACEHOLDER;
  return (
    <ol className="relative">
      {list.map((s, i) => (
        <li key={s.key} data-testid={`stage-${s.key}`} data-status={s.status} className="relative flex gap-3.5 pb-4 last:pb-0">
          {i < list.length - 1 && (
            <span className={clsx("absolute top-6 bottom-0 left-[11px] w-px", s.status === "done" ? "bg-accent/40" : "bg-line-2")} />
          )}
          <span className={clsx(
            "relative z-[1] grid h-6 w-6 shrink-0 place-items-center rounded-full border text-[10px]",
            s.status === "done" && "border-accent/60 bg-accent/15 text-accent",
            s.status === "running" && "border-accent bg-bg text-accent",
            s.status === "failed" && "border-bad bg-bad/15 text-bad",
            s.status === "pending" && "border-line-2 bg-bg text-faint",
          )}>
            {s.status === "done" ? <Icon name="check" className="h-3.5 w-3.5" /> :
              s.status === "running" ? <span className="pulse-dot h-2 w-2 rounded-full bg-accent" /> :
              s.status === "failed" ? <Icon name="x" className="h-3.5 w-3.5" /> : i + 1}
          </span>
          <div className="min-w-0 flex-1 pt-0.5">
            <div className="flex items-baseline justify-between gap-3">
              <span className={clsx("font-mono text-[12px] tracking-[0.12em] uppercase", s.status === "pending" ? "text-faint" : "text-text")}>
                {s.label}
              </span>
              <span className="tabular text-[11.5px] text-faint">{s.status === "running" ? "running…" : duration(s)}</span>
            </div>
            {!compact && s.detail && <p className={clsx("mt-0.5 text-[12.5px]", s.status === "failed" ? "text-[#991b1b]" : "text-muted")}>{s.detail}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}
