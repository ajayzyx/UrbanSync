import clsx from "clsx";
import { conflictTypeLabel, pct } from "@/lib/format";
import type { ConflictOut } from "@/lib/types";
import { ConflictStatusPill } from "../ui/StatusPill";
import { observedText } from "./observed";

export function ConflictTable({ rows, selected, onSelect }: { rows: ConflictOut[]; selected: number | null; onSelect: (c: ConflictOut) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-left text-[13px]">
        <thead>
          <tr className="micro border-b border-line">
            <th className="px-3 py-2 font-normal">Parcel</th>
            <th className="px-3 py-2 font-normal">Type</th>
            <th className="hidden px-3 py-2 font-normal 2xl:table-cell">Sources</th>
            <th className="px-3 py-2 font-normal">Observed</th>
            <th className="px-3 py-2 text-right font-normal">Conf.</th>
            <th className="px-3 py-2 font-normal">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id} onClick={() => onSelect(c)} aria-selected={selected === c.id}
              className={clsx("cursor-pointer border-b border-line/60 transition-colors last:border-0",
                selected === c.id ? "bg-accent/[0.07]" : "hover:bg-black/[0.02]")}>
              <td className="px-3 py-2.5 font-mono text-[12px]">{c.parcel_id}</td>
              <td className="px-3 py-2.5 whitespace-nowrap">{conflictTypeLabel(c.conflict_type)}</td>
              <td className="hidden px-3 py-2.5 whitespace-nowrap text-muted 2xl:table-cell">{c.source_a} → {c.source_b}</td>
              <td className="max-w-[220px] truncate px-3 py-2.5 text-muted" title={observedText(c)}>{observedText(c)}</td>
              <td className="tabular px-3 py-2.5 text-right">{pct(c.confidence)}</td>
              <td className="px-3 py-2.5"><ConflictStatusPill status={c.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
