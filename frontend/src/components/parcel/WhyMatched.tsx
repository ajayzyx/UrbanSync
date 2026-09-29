import { SOURCE_LABELS, pct } from "@/lib/format";
import type { MatchOut } from "@/lib/types";
import { StatusPill } from "../ui/StatusPill";
import { ConfidenceBars } from "./ConfidenceBars";

export function ExplanationLines({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <ul className="space-y-1 text-[12.5px] leading-snug">
      {lines.slice(1).map((l, i) => {
        const mark = l[0];
        if (l.startsWith("Reason:"))
          return (
            <li key={i} className="mt-2 border-l-2 border-accent/60 pl-2.5 text-text/90">
              <span className="text-muted">Reason:</span> {l.replace("Reason: ", "")}
            </li>
          );
        if (l.startsWith("Overall confidence"))
          return <li key={i} className="mt-1.5 font-medium text-text">{l}</li>;
        const color = mark === "✓" ? "#15803d" : mark === "!" ? "#b45309" : "#8b94a0";
        return (
          <li key={i} className="flex gap-2">
            <span className="w-3 shrink-0 text-center font-semibold" style={{ color }}>{mark}</span>
            <span className="text-text/85">{l.slice(2)}</span>
          </li>
        );
      })}
    </ul>
  );
}

export function WhyMatched({ matches }: { matches: MatchOut[] }) {
  const primary = matches.filter((m) => !m.is_duplicate);
  if (!primary.length) return <p className="text-[13px] text-muted">No cross-source match was found for this parcel.</p>;
  return (
    <div className="space-y-3">
      {primary.map((m) => (
        <div key={m.id} className="rounded-lg border border-line bg-panel-2 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-[12.5px]">
              <span className="text-muted">Cadastral ↔ </span>
              {SOURCE_LABELS[m.source_type] ?? m.source_type} <span className="font-mono text-[11.5px] text-muted">{m.record_id}</span>
            </div>
            <StatusPill status={m.match_class} label={`${pct(m.final_confidence)} · ${m.match_class === "HIGH" ? "High" : m.match_class === "REVIEW" ? "Review" : "Conflict"}`} />
          </div>
          <ExplanationLines text={m.explanation} />
          {typeof m.evidence.ml_probability === "number" && (
            <p className="mt-2 text-[11.5px] text-muted">
              Independent ML check (logistic regression, trained on a separate synthetic ward):{" "}
              <span className="tabular text-text">{pct(m.evidence.ml_probability as number)}</span> match probability
            </p>
          )}
          <details className="mt-3 group">
            <summary className="micro cursor-pointer select-none hover:text-text">Component scores</summary>
            <div className="mt-2"><ConfidenceBars components={m.components} /></div>
          </details>
        </div>
      ))}
    </div>
  );
}
