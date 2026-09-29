import Link from "next/link";
import { conflictTypeLabel } from "@/lib/format";
import type { ConflictOut } from "@/lib/types";
import { observedText } from "../conflicts/observed";

export function RecentConflicts({ rows }: { rows: ConflictOut[] }) {
  if (!rows.length) return <p className="text-[13px] text-muted">No pending conflicts.</p>;
  return (
    <ul className="divide-y divide-line/60">
      {rows.map((c) => (
        <li key={c.id}>
          <Link href={`/app/conflicts?id=${c.id}`} className="flex items-center justify-between gap-3 py-2 text-[13px] hover:text-accent">
            <span className="min-w-0">
              <span className="font-mono text-[12px]">{c.parcel_id}</span>{" "}
              <span className="text-muted">· {conflictTypeLabel(c.conflict_type)}</span>
              <span className="block truncate text-[12px] text-faint">{observedText(c)}</span>
            </span>
            <span className="shrink-0 text-[11px] text-warn">Pending</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
