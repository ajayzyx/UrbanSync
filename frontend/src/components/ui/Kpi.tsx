import type { ReactNode } from "react";

export function Kpi({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel/80 px-4 py-3">
      <div className="micro">{label}</div>
      <div className="font-display tabular mt-1 text-[26px] leading-tight font-medium" style={tone ? { color: tone } : undefined}>
        {value}
      </div>
      {sub && <div className="mt-0.5 text-[12px] text-muted">{sub}</div>}
    </div>
  );
}
