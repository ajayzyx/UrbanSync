import { pct, SOURCE_LABELS } from "@/lib/format";
import type { Mapping } from "@/lib/types";

const SHOWN = ["cadastral", "municipal", "revenue"];

export function AttributeMappingTable({ rows }: { rows: Mapping[] }) {
  const shown = rows.filter((r) => SHOWN.includes(r.source_type) && r.canonical_field);
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-left text-[13px]">
        <thead>
          <tr className="micro border-b border-line">
            <th className="py-2 pr-3 font-normal">Source</th>
            <th className="py-2 pr-3 font-normal">Source field</th>
            <th className="py-2 pr-3 font-normal">Canonical field</th>
            <th className="py-2 pr-3 font-normal">Confidence</th>
            <th className="py-2 font-normal">Method</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((r, i) => (
            <tr key={i} className="border-b border-line/60 last:border-0">
              <td className="py-2 pr-3 text-muted">{SOURCE_LABELS[r.source_type]}</td>
              <td className="py-2 pr-3 font-mono text-[12px]">{r.source_field}</td>
              <td className="py-2 pr-3 font-mono text-[12px] text-accent">→ {r.canonical_field}</td>
              <td className="py-2 pr-3">
                <span className="inline-flex items-center gap-2">
                  <span className="h-1.5 w-16 overflow-hidden rounded-full bg-black/[0.06]">
                    <span className="block h-full rounded-full bg-accent" style={{ width: `${r.confidence * 100}%` }} />
                  </span>
                  <span className="tabular text-[12px]">{pct(r.confidence)}</span>
                </span>
              </td>
              <td className="py-2 text-[12px] text-muted">{r.method}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
