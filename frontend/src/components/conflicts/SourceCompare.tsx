import clsx from "clsx";
import { fmtValue, SOURCE_LABELS } from "@/lib/format";
import type { SourceValues } from "@/lib/types";

const FIELDS: [string, string][] = [
  ["record_id", "Record"],
  ["owner_name", "Owner"],
  ["area", "Mapped area (m²)"],
  ["recorded_area", "Recorded area (m²)"],
  ["land_use", "Land use"],
  ["survey_date", "Record date"],
];
const ORDER = ["cadastral", "municipal", "revenue"];

function norm(v: unknown) {
  if (typeof v === "number") return Math.round(v);
  return typeof v === "string" ? v.toLowerCase().replace(/[^a-z0-9]/g, "") : v;
}

export function SourceCompare({ values, focusField }: { values: SourceValues; focusField: string | null }) {
  const sources = ORDER.filter((s) => values[s]);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[12.5px]">
        <thead>
          <tr className="micro border-b border-line">
            <th className="py-2 pr-3 font-normal">Field</th>
            {sources.map((s) => <th key={s} className="py-2 pr-3 font-normal">{SOURCE_LABELS[s]}</th>)}
          </tr>
        </thead>
        <tbody>
          {FIELDS.map(([f, label]) => {
            const vals = sources.map((s) => values[s]?.[f]);
            const present = vals.filter((v) => v !== null && v !== undefined).map(norm);
            const differs = !["record_id", "survey_date", "recorded_area"].includes(f) && (new Set(present).size > 1 || present.length < vals.length);
            return (
              <tr key={f} className={clsx("border-b border-line/60 last:border-0", f === focusField && "bg-warn/[0.06]")}>
                <td className="py-2 pr-3 text-muted">{label}</td>
                {vals.map((v, i) => (
                  <td key={sources[i]} className={clsx("py-2 pr-3", f === "record_id" && "font-mono text-[11.5px]",
                    differs && "font-medium text-warn")}>
                    {fmtValue(v)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
