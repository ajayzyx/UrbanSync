import { pct } from "@/lib/format";
import type { Components } from "@/lib/types";

export const WEIGHTS: { key: keyof Components; label: string; weight: number }[] = [
  { key: "geometry", label: "Geometry overlap", weight: 0.3 },
  { key: "centroid", label: "Centroid proximity", weight: 0.2 },
  { key: "area", label: "Area similarity", weight: 0.15 },
  { key: "shape", label: "Boundary shape", weight: 0.15 },
  { key: "attribute", label: "Attribute (owner)", weight: 0.1 },
  { key: "temporal", label: "Temporal consistency", weight: 0.1 },
];

function tone(v: number) {
  return v >= 0.8 ? "#15803d" : v < 0.6 ? "#b91c1c" : "#b45309";
}

export function ConfidenceBars({ components }: { components: Components }) {
  return (
    <div className="space-y-1.5">
      {WEIGHTS.map(({ key, label, weight }) => {
        const v = components[key];
        return (
          <div key={key} className="grid grid-cols-[1fr_90px_38px] items-center gap-2 text-[12px]">
            <span className="truncate text-muted">
              {label} <span className="text-faint">· {Math.round(weight * 100)}%</span>
            </span>
            <span className="h-1.5 overflow-hidden rounded-full bg-black/[0.06]">
              {v !== null && <span className="block h-full rounded-full" style={{ width: `${v * 100}%`, background: tone(v) }} />}
            </span>
            <span className="tabular text-right">{v === null ? <span className="text-faint">n/a</span> : pct(v)}</span>
          </div>
        );
      })}
    </div>
  );
}
