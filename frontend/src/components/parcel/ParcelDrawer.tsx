"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useApi } from "@/lib/api";
import { conflictTypeLabel, fmtArea, fmtTime, fmtValue, parcelStatusLabel, pct, SOURCE_LABELS, statusColor } from "@/lib/format";
import type { ParcelDetail } from "@/lib/types";
import { Icon } from "../ui/Icon";
import { ErrorState, Skeleton } from "../ui/States";
import { ConflictStatusPill, StatusPill } from "../ui/StatusPill";
import { Provenance } from "./Provenance";
import { WhyMatched } from "./WhyMatched";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-line px-5 py-4">
      <h3 className="micro mb-2.5">{title}</h3>
      {children}
    </section>
  );
}

const TOPO_LABEL = { VALID: "Valid", ISSUE: "Issue — review", SUGGESTED_FIX: "Safe fix applied (source unchanged)" };

export function ParcelDrawer({ parcelId, version = 0, onClose }: { parcelId: string; version?: number; onClose: () => void }) {
  const { data: p, error, loading, reload } = useApi<ParcelDetail>(`/parcels/${encodeURIComponent(parcelId)}?v=${version}`);
  const has = (t: string) => p?.provenance.some((x) => x.source_type === t);

  return (
    <aside
      className="fixed inset-0 z-50 flex flex-col overflow-hidden bg-panel md:absolute md:inset-y-3 md:right-3 md:left-auto md:w-[420px] md:rounded-xl md:border md:border-line-2 md:shadow-2xl md:shadow-black/15"
      aria-label={`Parcel ${parcelId} details`}>
      <header className="flex items-start justify-between gap-3 px-5 pt-4 pb-3">
        <div>
          <div className="micro">Canonical parcel</div>
          <div className="font-display mt-0.5 text-[22px] font-medium">{parcelId}</div>
          {p && <div className="mt-1.5"><StatusPill status={p.match_status} label={parcelStatusLabel(p.match_status, p.matches.filter((m) => !m.is_duplicate).map((m) => m.match_class))} /></div>}
        </div>
        <button onClick={onClose} aria-label="Close parcel details"
          className="rounded-md border border-line p-1.5 text-muted hover:text-text"><Icon name="x" /></button>
      </header>

      <div className="flex-1 overflow-y-auto">
        {loading && !p && (
          <div className="space-y-3 px-5 py-4">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        )}
        {error && <ErrorState message={error.message} onRetry={reload} />}
        {p && (
          <>
            <div className="grid grid-cols-2 gap-x-4 gap-y-3 px-5 pb-4 text-[13px]">
              <div className="col-span-2">
                <div className="micro">Owner</div>
                <div className="mt-0.5 text-[15px]">{p.owner_name ?? "—"}
                  {p.resolved_values.owner_name && <ResolvedTag />}</div>
              </div>
              <div>
                <div className="micro">Area</div>
                <div className="tabular mt-0.5">{fmtArea(p.area)}{p.resolved_values.area && <ResolvedTag />}</div>
              </div>
              <div>
                <div className="micro">Land use</div>
                <div className="mt-0.5">{p.land_use ?? "—"}{p.resolved_values.land_use && <ResolvedTag />}</div>
              </div>
              <div>
                <div className="micro">Match confidence</div>
                <div className="font-display tabular mt-0.5 text-[26px] leading-none" style={{ color: statusColor(p.match_status) }}>
                  {pct(p.confidence_score)}
                </div>
              </div>
              <div>
                <div className="micro">Topology</div>
                <div className="mt-0.5" style={{ color: p.topology_status === "VALID" ? "#15803d" : "#b45309" }}>
                  {TOPO_LABEL[p.topology_status]}
                </div>
              </div>
            </div>

            <Section title="Sources">
              <ul className="grid grid-cols-2 gap-1.5 text-[12.5px]">
                {[
                  ["Cadastral", has("cadastral")],
                  ["Revenue", has("revenue")],
                  ["Municipal", has("municipal")],
                  [`GNSS (${p.gnss_count})`, p.gnss_count > 0],
                  [`Buildings (${p.building_count})`, p.building_count > 0],
                ].map(([label, ok]) => (
                  <li key={String(label)} className="flex items-center gap-2">
                    <span className={ok ? "text-ok" : "text-faint"}>{ok ? "✓" : "✗"}</span>
                    <span className={ok ? "" : "text-faint"}>{label}</span>
                  </li>
                ))}
              </ul>
            </Section>

            <Section title="Why was this matched?">
              <WhyMatched matches={p.matches} />
            </Section>

            {Object.keys(p.resolved_values).length > 0 && (
              <Section title="Reviewer-resolved values">
                <ul className="space-y-1.5 text-[12.5px]">
                  {Object.entries(p.resolved_values).map(([field, rv]) => (
                    <li key={field} className="rounded-md border border-accent/25 bg-accent/5 px-2.5 py-1.5">
                      <span className="text-muted">{field.replace("_", " ")}:</span> {fmtValue(rv.value)}{" "}
                      <span className="text-faint">from {SOURCE_LABELS[rv.source] ?? rv.source} · {fmtTime(rv.resolved_at)}</span>
                      {rv.note && <div className="text-faint">“{rv.note}”</div>}
                    </li>
                  ))}
                </ul>
                <p className="mt-2 text-[11.5px] text-faint">Stored separately from source records, which remain unchanged.</p>
              </Section>
            )}

            <Section title={`Conflicts (${p.conflicts.filter((c) => c.status === "Pending Review").length} pending)`}>
              {p.conflicts.length === 0 ? (
                <p className="text-[12.5px] text-muted">No conflicts detected.</p>
              ) : (
                <ul className="space-y-1.5">
                  {p.conflicts.map((c) => (
                    <li key={c.id}>
                      <Link href={`/app/conflicts?id=${c.id}`}
                        className="flex items-center justify-between gap-2 rounded-md border border-line px-2.5 py-1.5 text-[12.5px] hover:border-accent/40">
                        <span>{conflictTypeLabel(c.conflict_type)} <span className="text-faint">· {c.source_b}</span></span>
                        <ConflictStatusPill status={c.status} />
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section title="Provenance">
              <Provenance items={p.provenance} />
            </Section>
          </>
        )}
      </div>
      <footer className="border-t border-line px-5 py-2.5 text-[11px] text-faint">
        {p?.disclaimer ?? "Decision-support only — not a legal determination of ownership."}
      </footer>
    </aside>
  );
}

function ResolvedTag() {
  return <span className="ml-2 rounded border border-accent/40 px-1 py-px align-middle text-[10px] text-accent">Reviewer-resolved</span>;
}
