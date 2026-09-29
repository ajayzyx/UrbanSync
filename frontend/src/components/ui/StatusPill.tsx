import { classLabel, statusColor } from "@/lib/format";
import type { MatchClass, MatchStatus } from "@/lib/types";

export function StatusPill({ status, label }: { status: MatchStatus | MatchClass; label?: string }) {
  const c = statusColor(status);
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium"
      style={{ color: c, borderColor: `${c}55`, background: `${c}14` }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: c }} />
      {label ?? classLabel(status)}
    </span>
  );
}

const CONFLICT_STATUS: Record<string, string> = {
  "Pending Review": "#b45309",
  Accepted: "#0f766e",
  Resolved: "#15803d",
  Ignored: "#64748b",
};

export function ConflictStatusPill({ status }: { status: string }) {
  const c = CONFLICT_STATUS[status] ?? "#64748b";
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px]"
      style={{ color: c, borderColor: `${c}55`, background: `${c}12` }}>
      {status}
    </span>
  );
}
