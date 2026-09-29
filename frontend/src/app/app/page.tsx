"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { DatasetTable } from "@/components/dashboard/DatasetTable";
import { Pipeline } from "@/components/dashboard/Pipeline";
import { RecentConflicts } from "@/components/dashboard/RecentConflicts";
import { DEFAULT_VISIBLE } from "@/components/map/layers";
import { Icon } from "@/components/ui/Icon";
import { Kpi } from "@/components/ui/Kpi";
import { Panel } from "@/components/ui/Panel";
import { PageHeader } from "@/components/ui/Shell";
import { EmptyState, ErrorState, RunFirstCta, Skeleton } from "@/components/ui/States";
import { useApi } from "@/lib/api";
import { demoCity, STATIC_CITIES, type CityProfile } from "@/lib/cities";
import { fmtNum, pct, STATUS_COLORS } from "@/lib/format";
import type { Analytics, ConflictOut, Dataset } from "@/lib/types";

const GisMap = dynamic(() => import("@/components/map/GisMap"), { ssr: false });
const PREVIEW_LAYERS = { ...DEFAULT_VISIBLE, buildings: false, topology: false };

export default function CommandCenter() {
  const a = useApi<Analytics>("/analytics");
  const ds = useApi<Dataset[]>("/datasets");
  const recent = useApi<ConflictOut[]>("/conflicts?status=Pending%20Review&limit=400");
  const cities = useApi<CityProfile[]>("/cities");
  // one example per conflict type gives the reviewer a representative queue
  const sample = recent.data
    ? [...new Map([...recent.data].reverse().map((c) => [c.conflict_type, c] as const)).values()].reverse().slice(0, 6)
    : null;
  const k = a.data?.kpis;
  const hasRun = !!a.data?.run && (k?.parcels ?? 0) > 0;

  return (
    <>
      <PageHeader eyebrow="Command Center" title="Different departments, one trusted parcel view.">
        <Link href="/app/india" className="inline-flex items-center gap-2 rounded-full border border-line-2 bg-panel px-3 py-2 text-[12.5px] text-muted hover:border-accent/50 hover:text-accent">
          <Icon name="globe" className="h-3.5 w-3.5" />
          India · {(cities.data ?? STATIC_CITIES).length} city profiles · {(cities.data ?? STATIC_CITIES).filter((c) => c.status === "demo").length} active demo dataset
        </Link>
        <Link href="/app/harmonize" className="inline-flex items-center gap-2 rounded-lg border border-line-2 px-3 py-2 text-[13px] hover:border-accent/50">
          <Icon name="flow" /> Harmonization
        </Link>
      </PageHeader>
      <div className="space-y-4 px-4 pb-8 md:px-6">
        {a.loading && !a.data && <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-20" />)}</div>}
        {a.error && <Panel><ErrorState message={a.error.message} onRetry={a.reload} /></Panel>}
        {a.data && !hasRun && (
          <Panel>
            <EmptyState title="No harmonization run yet"
              body="Datasets are loaded. Run the first harmonization to normalize, match, validate and score every parcel."
              action={<RunFirstCta />} />
          </Panel>
        )}
        {a.data && hasRun && k && (
          <>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
              <Kpi label="Parcels" value={fmtNum(k.parcels)} sub={`${k.datasets} datasets`} />
              <Kpi label="Matched" value={fmtNum(k.matched)} sub="cross-source links" />
              <Kpi label="High confidence" value={fmtNum(k.high)} sub={<span style={{ color: STATUS_COLORS.HARMONIZED }}>● harmonized</span>} />
              <Kpi label="Review" value={fmtNum(k.review)} sub={<span style={{ color: STATUS_COLORS.REVIEW }}>● needs a look</span>} />
              <Kpi label="Conflicts pending" value={fmtNum(k.conflicts_pending)} sub={`${fmtNum(k.conflicts_resolved)} resolved`} />
              <Kpi label="Topology issues" value={fmtNum(k.topology_issues)} sub="overlaps · gaps · invalid" />
              <Kpi label="Avg confidence" value={pct(k.avg_confidence, 1)} sub="explainable score" />
              <Kpi label="Last run"
                value={k.last_run_at ? new Date(k.last_run_at).toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" }) : "—"}
                sub={`${k.last_run_at ? new Date(k.last_run_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : ""} · ${a.data.run?.summary.duration_s ?? "—"} s run`} />
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
              <Panel eyebrow="Map preview" title={`${demoCity(cities.data).name} · Demo ward — harmonized parcels`}
                actions={<Link href="/app/map" className="text-[12.5px] text-accent hover:underline">Open Web GIS →</Link>} bodyClassName="p-0">
                <div className="relative h-[300px] overflow-hidden rounded-b-xl">
                  <GisMap compact visible={PREVIEW_LAYERS} />
                </div>
              </Panel>
              <Panel eyebrow={`Run #${a.data.run?.id}`} title="Harmonization pipeline">
                <Pipeline stages={a.data.run?.stages} compact />
              </Panel>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
              <Panel eyebrow="Resolve" title="Conflict queue — one per type"
                actions={<Link href="/app/conflicts" className="text-[12.5px] text-accent hover:underline">All →</Link>}>
                {sample ? <RecentConflicts rows={sample} /> : <Skeleton className="h-40" />}
              </Panel>
              <Panel eyebrow="Integrate" title="Dataset health" bodyClassName="px-4 py-1">
                {ds.data ? <DatasetTable datasets={ds.data} compact /> : <Skeleton className="h-40" />}
              </Panel>
            </div>
          </>
        )}
      </div>
    </>
  );
}
