import { fmtNum, fmtTime, SOURCE_LABELS } from "@/lib/format";
import type { Dataset } from "@/lib/types";

const STATUS_TONE: Record<string, string> = { processed: "#15803d", ingested: "#0f766e", registered: "#8b94a0", error: "#b91c1c" };

export function DatasetStatus({ status }: { status: string }) {
  const c = STATUS_TONE[status] ?? "#8b94a0";
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] capitalize" style={{ color: c }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: c }} />{status}
    </span>
  );
}

export function DatasetTable({ datasets, compact = false }: { datasets: Dataset[]; compact?: boolean }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-[13px]">
        <thead>
          <tr className="micro border-b border-line">
            <th className="py-2 pr-3 font-normal">Source</th>
            {!compact && <th className="py-2 pr-3 font-normal">Type</th>}
            <th className="py-2 pr-3 text-right font-normal">Records</th>
            <th className="py-2 pr-3 font-normal">CRS</th>
            <th className="py-2 pr-3 font-normal">Status</th>
            {!compact && <th className="py-2 font-normal">Last processed</th>}
          </tr>
        </thead>
        <tbody>
          {datasets.map((d) => {
            const registered = d.status === "registered";
            const update = d.metadata?.role === "update";
            return (
              <tr key={d.id} className="border-b border-line/60 last:border-0">
                <td className="py-2.5 pr-3">
                  <div>{d.name}{d.version > 1 && <span className="ml-1.5 text-faint">v{d.version}</span>}</div>
                  {registered && <div className="text-[11.5px] text-faint">Registered — metadata &amp; footprint only</div>}
                  {update && <div className="text-[11.5px] text-faint">Incoming update — used for change detection</div>}
                </td>
                {!compact && <td className="py-2.5 pr-3 text-muted">{SOURCE_LABELS[d.source_type] ?? d.source_type}</td>}
                <td className="tabular py-2.5 pr-3 text-right">{registered ? "—" : fmtNum(d.record_count)}</td>
                <td className="py-2.5 pr-3 font-mono text-[11.5px] whitespace-nowrap">
                  {d.source_crs ?? "—"}
                  {!registered && d.source_crs !== d.target_crs && <span className="text-accent"> → {d.target_crs}</span>}
                </td>
                <td className="py-2.5 pr-3"><DatasetStatus status={d.status} /></td>
                {!compact && <td className="py-2.5 text-muted">{fmtTime(d.last_processed)}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
