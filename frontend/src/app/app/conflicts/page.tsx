"use client";

import clsx from "clsx";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ConflictDetail } from "@/components/conflicts/ConflictDetail";
import { ConflictTable } from "@/components/conflicts/ConflictTable";
import { DEFAULT_VISIBLE } from "@/components/map/layers";
import { Panel } from "@/components/ui/Panel";
import { PageHeader } from "@/components/ui/Shell";
import { EmptyState, ErrorState, RunFirstCta, Skeleton } from "@/components/ui/States";
import { useApi } from "@/lib/api";
import type { ConflictOut } from "@/lib/types";

const GisMap = dynamic(() => import("@/components/map/GisMap"), { ssr: false });
const FILTERS = [["all", "All"], ["area", "Area"], ["boundary", "Boundary"], ["attribute", "Attribute"], ["duplicate", "Duplicate"], ["topology", "Topology"]];
const STATUSES = ["Pending Review", "Resolved", "Accepted", "Ignored", "All"];
const MAP_LAYERS = { ...DEFAULT_VISIBLE, buildings: false, municipal: true, topology: true };

function ConflictCenter() {
  const params = useSearchParams();
  const router = useRouter();
  const type = params.get("type") ?? "all";
  const status = params.get("status") ?? "Pending Review";
  const id = params.get("id") ? Number(params.get("id")) : null;
  const q = new URLSearchParams({ limit: "500" });
  if (type !== "all") q.set("type", type);
  if (status !== "All") q.set("status", status);
  const { data, error, loading, reload } = useApi<ConflictOut[]>(`/conflicts?${q}`);
  const { data: detail } = useApi<ConflictOut>(id ? `/conflicts/${id}` : null);
  const [version, setVersion] = useState(0);

  const nav = (next: Record<string, string | null>) => {
    const p = new URLSearchParams(params.toString());
    Object.entries(next).forEach(([k, v]) => (v === null ? p.delete(k) : p.set(k, v)));
    router.replace(`/app/conflicts?${p}`, { scroll: false });
  };

  return (
    <>
      <PageHeader eyebrow="Resolve" title="Conflict Center" />
      <div className="px-4 pb-8 md:px-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {FILTERS.map(([k, label]) => (
            <button key={k} onClick={() => nav({ type: k === "all" ? null : k, id: null })} aria-pressed={type === k}
              className={clsx("rounded-full border px-3 py-1 text-[12.5px]",
                type === k ? "border-accent/60 bg-accent/10 text-accent" : "border-line-2 text-muted hover:text-text")}>
              {label}
            </button>
          ))}
          <select value={status} onChange={(e) => nav({ status: e.target.value, id: null })} aria-label="Status filter"
            className="ml-auto rounded-lg border border-line-2 bg-panel px-2.5 py-1.5 text-[12.5px]">
            {STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
          <Panel bodyClassName="p-0" title={data ? `${data.length} conflicts` : "Conflicts"} eyebrow={status}>
            {loading && !data && <div className="space-y-2 p-4">{[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-8" />)}</div>}
            {error && <ErrorState message={error.message} onRetry={reload} />}
            {data && data.length === 0 && (
              <EmptyState title="No conflicts match this filter" body="Try another type or status — or run a harmonization first."
                action={<RunFirstCta />} />
            )}
            {data && data.length > 0 && (
              <div className="max-h-[70vh] overflow-y-auto">
                <ConflictTable rows={data} selected={id} onSelect={(c) => nav({ id: String(c.id) })} />
              </div>
            )}
          </Panel>

          <div className="space-y-4">
            <div className="relative h-[260px] overflow-hidden rounded-xl border border-line">
              <GisMap compact visible={MAP_LAYERS} selectedParcel={detail?.parcel_id ?? null}
                focusBbox={detail?.bbox ?? null} dataVersion={version} />
            </div>
            <Panel bodyClassName="p-0">
              {id ? (
                <ConflictDetail key={id} id={id} onResolved={() => { reload(); setVersion((v) => v + 1); }} />
              ) : (
                <EmptyState title="Select a conflict" body="Open a row to see why it was flagged, compare source values and record a decision." />
              )}
            </Panel>
          </div>
        </div>
      </div>
    </>
  );
}

export default function ConflictsPage() {
  return (
    <Suspense fallback={<div className="p-6"><Skeleton className="h-[60vh]" /></div>}>
      <ConflictCenter />
    </Suspense>
  );
}
