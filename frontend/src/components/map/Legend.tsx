import { STATUS_COLORS } from "@/lib/format";

export function Legend({ changes }: { changes: boolean }) {
  const items = changes
    ? [["New", "#15803d"], ["Modified", "#b45309"], ["Removed", "#b91c1c"]]
    : [["High confidence", STATUS_COLORS.HARMONIZED], ["Review", STATUS_COLORS.REVIEW], ["Conflict", STATUS_COLORS.CONFLICT],
       ["Topology issue", "#b91c1c"]];
  return (
    <div className="rounded-lg border border-line bg-panel/95 px-3 py-2 text-[11.5px] shadow-sm backdrop-blur">
      <div className="micro mb-1.5">{changes ? "Change (municipal v1 → v2)" : "Match status"}</div>
      <ul className="space-y-1">
        {items.map(([label, c], i) => (
          <li key={label} className="flex items-center gap-2">
            <span className={i === 3 ? "h-2.5 w-2.5 border" : "h-2.5 w-2.5 rounded-sm"}
              style={i === 3 ? { borderColor: c, background: `${c}66` } : { background: c }} />
            {label}
          </li>
        ))}
      </ul>
    </div>
  );
}
