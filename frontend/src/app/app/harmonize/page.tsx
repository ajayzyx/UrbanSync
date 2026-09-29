"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AttributeMappingTable } from "@/components/dashboard/AttributeMappingTable";
import { Pipeline } from "@/components/dashboard/Pipeline";
import { Icon } from "@/components/ui/Icon";
import { Button, Panel } from "@/components/ui/Panel";
import { PageHeader } from "@/components/ui/Shell";
import { ErrorState } from "@/components/ui/States";
import { useToast } from "@/components/ui/Toast";
import { apiGet, apiPost, pollRun, type ApiError } from "@/lib/api";
import { fmtNum, pct } from "@/lib/format";
import type { Mapping, Run } from "@/lib/types";

export default function HarmonizePage() {
  const [run, setRun] = useState<Run | null>(null);
  const [mappings, setMappings] = useState<Mapping[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const stop = useRef<(() => void) | null>(null);
  const toast = useToast();

  const follow = (id: number) => {
    stop.current?.();
    stop.current = pollRun(id, (r) => {
      setRun(r);
      if (r.status === "completed") {
        apiGet<Mapping[]>(`/harmonization/${r.id}/mappings`).then(setMappings).catch(() => setMappings([]));
      }
    }, (e) => setError(e.message));
  };

  useEffect(() => {
    apiGet<Run>("/harmonization/latest").then((r) => follow(r.id)).catch((e: ApiError) => {
      if (e.status !== 404) setError(e.message);
    });
    return () => stop.current?.();
  }, []);

  const start = async () => {
    setStarting(true);
    setError(null);
    setMappings(null);
    stop.current?.();
    setRun(null); // show the new run's pending stages, never the previous run's finished ones
    try {
      const { run_id } = await apiPost<{ run_id: number }>("/harmonize");
      follow(run_id);
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 409) {
        toast("A run is already in progress — showing it", "info");
        apiGet<Run>("/harmonization/latest").then((r) => follow(r.id));
      } else setError(err.message);
    } finally {
      setStarting(false);
    }
  };

  const running = run?.status === "running";
  const s = run?.summary ?? {};
  const done = run?.status === "completed";

  return (
    <>
      <PageHeader eyebrow="Harmonize" title="Harmonization Workspace">
        <Button variant="primary" onClick={start} disabled={running || starting}>
          <Icon name="play" className="h-3.5 w-3.5" /> {running ? "Running…" : done ? "Re-run harmonization" : "Run harmonization"}
        </Button>
      </PageHeader>
      <div className="grid grid-cols-1 gap-4 px-4 pb-8 md:px-6 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
        <Panel eyebrow={run ? `Run #${run.id} · ${run.status}` : "No run yet"} title="Pipeline">
          {error ? <ErrorState message={error} onRetry={start} /> : <Pipeline stages={run?.stages} />}
          {run?.status === "failed" && run.error && <p className="mt-3 text-[12.5px] text-[#991b1b]">Run failed: {run.error}</p>}
          <p className="mt-4 text-[11.5px] text-faint">Stage states and details are reported by the backend as each step completes.</p>
        </Panel>

        <div className="space-y-4">
          {done ? (
            <>
              <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
                {[
                  ["Parcels", fmtNum(s.parcels)],
                  ["Matched (municipal)", fmtNum(s.matched)],
                  ["Conflicts", fmtNum(s.conflicts)],
                  ["Avg confidence", pct(s.avg_confidence, 1)],
                ].map(([k, v]) => (
                  <div key={k} className="rounded-xl border border-line bg-panel/80 px-4 py-3">
                    <div className="micro">{k}</div>
                    <div className="font-display tabular mt-1 text-[24px]">{v}</div>
                  </div>
                ))}
              </div>
              <Panel eyebrow="Normalize" title="Coordinate systems">
                <ul className="flex flex-wrap gap-2 text-[12.5px]">
                  {s.crs_transforms?.map((t) => (
                    <li key={t.dataset} className="rounded-md border border-line bg-bg-2 px-2.5 py-1 font-mono text-[11.5px]">
                      {t.dataset}: {t.from} <span className="text-accent">→ {t.to}</span>
                    </li>
                  ))}
                </ul>
              </Panel>
              <Panel eyebrow="Map attributes" title="Schema mapping to canonical fields">
                {mappings ? <AttributeMappingTable rows={mappings} /> : <p className="text-[13px] text-muted">Loading mappings…</p>}
              </Panel>
              <div className="flex flex-wrap gap-2">
                <Link href="/app/map" className="inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-[13px] font-medium text-[#04211d]">
                  Open map <Icon name="arrow" className="h-3.5 w-3.5" />
                </Link>
                <Link href="/app/conflicts" className="inline-flex items-center gap-2 rounded-lg border border-line-2 px-3 py-2 text-[13px]">
                  Review conflicts <Icon name="arrow" className="h-3.5 w-3.5" />
                </Link>
              </div>
            </>
          ) : (
            <Panel title={running ? "Harmonizing…" : "What happens when you run"}>
              <ul className="space-y-2 text-[13px] text-muted">
                <li>• Every source is reprojected into one project CRS (EPSG:32643) and its geometry validated.</li>
                <li>• Municipal polygons and revenue records are matched to cadastral parcels with an explainable, weighted score.</li>
                <li>• Department schemas are mapped to canonical fields; conflicts and topology issues are queued for review.</li>
                <li>• Source records are never modified — every canonical parcel keeps full provenance.</li>
              </ul>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
}
