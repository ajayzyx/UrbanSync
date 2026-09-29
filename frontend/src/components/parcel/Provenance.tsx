import type { Provenance as P } from "@/lib/types";

const NOUN: Record<string, string> = {
  cadastral: "record", revenue: "Khasra", municipal: "property", gnss: "survey", buildings: "footprint",
};

export function Provenance({ items }: { items: P[] }) {
  return (
    <ul className="space-y-1 text-[12.5px]">
      {items.map((p) => (
        <li key={`${p.source_type}-${p.source_feature_id}`} className="flex items-baseline justify-between gap-3">
          <span className="text-muted">{p.label} <span className="text-faint">/ {NOUN[p.source_type] ?? "record"}</span></span>
          <span className="font-mono text-[11.5px]">{p.record_id}</span>
        </li>
      ))}
    </ul>
  );
}
