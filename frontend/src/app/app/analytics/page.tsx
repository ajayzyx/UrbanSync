"use client";

import { ConfidenceHistogram, conflictRows, HBars, MatchDistribution } from "@/components/dashboard/Charts";
import { Kpi } from "@/components/ui/Kpi";
import { Panel } from "@/components/ui/Panel";
import { PageHeader } from "@/components/ui/Shell";
import { EmptyState, ErrorState, RunFirstCta, Skeleton } from "@/components/ui/States";
import { useApi } from "@/lib/api";
import { fmtNum, pct } from "@/lib/format";
import type { Analytics } from "@/lib/types";

const TOPO_LABEL: Record<string, string> = { OVERLAP: "Overlap", GAP: "Gap", SELF_INTERSECTION: "Self-intersection", INVALID_GEOMETRY: "Invalid geometry" };

export default function AnalyticsPage() {
  const { data: a, error, loading, reload } = useApi<Analytics>("/analytics");
  const hasRun = !!a?.run && a.kpis.parcels > 0;
  const s = a?.run?.summary;

  return (
    <>
      <PageHeader eyebrow="Validate" title="Validation & Analytics" />
      <div className="space-y-4 px-4 pb-8 md:px-6">
        {loading && !a && <Skeleton className="h-64" />}
        {error && <Panel><ErrorState message={error.message} onRetry={reload} /></Panel>}
        {a && !hasRun && <Panel><EmptyState title="Nothing to analyse yet" body="Run a harmonization to generate match, conflict and quality metrics." action={<RunFirstCta />} /></Panel>}
        {a && hasRun && (
          <>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Panel eyebrow="Match" title="Match status distribution"><MatchDistribution data={a.match_distribution} /></Panel>
              <Panel eyebrow="Confidence" title="Confidence distribution (parcels)"><ConfidenceHistogram data={a.confidence_histogram} /></Panel>
              <Panel eyebrow="Conflicts" title="Conflict breakdown by type"><HBars data={conflictRows(a.conflict_breakdown)} /></Panel>
              <Panel eyebrow="Topology" title="Topology findings">
                <HBars data={a.topology_stats.map((t) => ({ name: TOPO_LABEL[t.type] ?? t.type, value: t.count }))} />
              </Panel>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
              <Panel eyebrow="Data quality" title="Before vs after harmonization">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[13px]">
                    <thead>
                      <tr className="micro border-b border-line">
                        <th className="py-2 pr-3 font-normal">Metric</th>
                        <th className="py-2 pr-3 text-right font-normal">Before</th>
                        <th className="py-2 text-right font-normal">After</th>
                      </tr>
                    </thead>
                    <tbody>
                      {a.quality_before_after.map((r) => (
                        <tr key={r.metric} className="border-b border-line/60 last:border-0">
                          <td className="py-2.5 pr-3">{r.metric}</td>
                          <td className="tabular py-2.5 pr-3 text-right text-muted">{fmtNum(r.before)}</td>
                          <td className="tabular py-2.5 text-right font-medium text-accent">{fmtNum(r.after)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>
              <Panel eyebrow="Processing summary" title={`Run #${a.run?.id}`}>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-[13px]">
                  <div><dt className="micro">Features processed</dt><dd className="tabular mt-0.5">{fmtNum(s?.features)}</dd></div>
                  <div><dt className="micro">End-to-end time</dt><dd className="tabular mt-0.5">{s?.duration_s} s</dd></div>
                  <div><dt className="micro">Revenue records linked</dt><dd className="tabular mt-0.5">{fmtNum(s?.revenue_matched)}</dd></div>
                  <div><dt className="micro">Avg confidence</dt><dd className="tabular mt-0.5">{pct(s?.avg_confidence, 1)}</dd></div>
                  <div className="col-span-2">
                    <dt className="micro">CRS transforms</dt>
                    <dd className="mt-1 flex flex-wrap gap-1.5">
                      {s?.crs_transforms?.map((t) => (
                        <span key={t.dataset} className="rounded border border-line px-1.5 py-0.5 font-mono text-[11px]">{t.dataset}: {t.from} → {t.to}</span>
                      ))}
                    </dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="micro">Municipal v1 → v2 changes</dt>
                    <dd className="tabular mt-0.5">
                      {Object.entries(s?.changes ?? {}).map(([k, v]) => `${v} ${k.toLowerCase()}`).join(" · ")}
                    </dd>
                  </div>
                </dl>
              </Panel>
            </div>

            {a.evaluation && (
              <Panel eyebrow="Evaluation" title="Evaluated on synthetic ground truth">
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
                  <Kpi label="Match precision" value={pct(a.evaluation.match_precision, 1)} />
                  <Kpi label="Match recall" value={pct(a.evaluation.match_recall, 1)} />
                  <Kpi label="Area-conflict recall" value={pct(a.evaluation.area_conflict_recall, 1)} />
                  <Kpi label="Owner-conflict recall" value={pct(a.evaluation.owner_conflict_recall, 1)} />
                  <Kpi label="Name-variant false alarms" value={pct(a.evaluation.owner_false_positive_rate, 1)} />
                  <Kpi label="ML check precision" value={pct(a.evaluation.ml_match_precision, 1)} sub="advisory model" />
                  <Kpi label="ML ↔ weighted agreement" value={pct(a.evaluation.ml_baseline_agreement, 1)} sub="independent check" />
                </div>
                <p className="mt-3 text-[12px] text-faint">
                  Measured against the answer key of the deterministic synthetic ward (seed 42) with injected discrepancies.
                  Real departmental data will score lower; these figures demonstrate the method, not field accuracy.
                </p>
              </Panel>
            )}
          </>
        )}
      </div>
    </>
  );
}
