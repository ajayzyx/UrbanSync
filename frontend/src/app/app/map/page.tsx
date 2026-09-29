"use client";

import clsx from "clsx";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useState } from "react";
import { Legend } from "@/components/map/Legend";
import { LayerControl } from "@/components/map/LayerControl";
import { MapSearch } from "@/components/map/MapSearch";
import { DEFAULT_VISIBLE, type LayerKey } from "@/components/map/layers";
import { ParcelDrawer } from "@/components/parcel/ParcelDrawer";
import { Icon } from "@/components/ui/Icon";
import { EmptyState, ErrorState, RunFirstCta, Skeleton } from "@/components/ui/States";
import { apiGet } from "@/lib/api";
import { demoCity } from "@/lib/cities";
import type { BBox, ParcelSummary } from "@/lib/types";

const GisMap = dynamic(() => import("@/components/map/GisMap"), { ssr: false });

function Toggle({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} aria-pressed={on}
      className={clsx("rounded-lg border px-3 py-2 text-[13px] whitespace-nowrap transition-colors",
        on ? "border-accent/50 bg-accent/10 text-accent" : "border-line-2 bg-panel/95 text-muted hover:text-text")}>
      {children}
    </button>
  );
}

function MapWorkspace() {
  const params = useSearchParams();
  const router = useRouter();
  const selected = params.get("parcel");
  const [visible, setVisible] = useState(DEFAULT_VISIBLE);
  const [confidence, setConfidence] = useState(true);
  const [conflictsOnly, setConflictsOnly] = useState(false);
  const [focus, setFocus] = useState<BBox | null>(null);
  const [fit, setFit] = useState(0);
  const [status, setStatus] = useState<{ loading: boolean; error: string | null; empty: boolean }>({ loading: true, error: null, empty: false });
  const [attempt, setAttempt] = useState(0);

  const select = useCallback((id: string | null, bbox?: BBox) => {
    router.replace(id ? `/app/map?parcel=${encodeURIComponent(id)}` : "/app/map", { scroll: false });
    if (bbox) setFocus(bbox);
  }, [router]);

  // fly to a parcel opened from a deep link
  const [lastDeepLink, setLastDeepLink] = useState<string | null>(null);
  if (selected && selected !== lastDeepLink) {
    setLastDeepLink(selected);
    apiGet<ParcelSummary[]>(`/parcels?q=${encodeURIComponent(selected)}&limit=1`)
      .then((r) => r[0]?.parcel_id === selected && setFocus(r[0].bbox)).catch(() => {});
  }

  const toggle = (k: LayerKey) => setVisible((v) => ({ ...v, [k]: !v[k] }));

  return (
    <div className="relative h-[calc(100dvh-56px-80px)] overflow-hidden md:h-[calc(100dvh-56px)]">
      <GisMap key={attempt} visible={visible} colorByConfidence={confidence} conflictsOnly={conflictsOnly}
        selectedParcel={selected} onSelect={(id) => select(id)} focusBbox={focus} fitSignal={fit} onStatus={setStatus} />

      <div className="absolute top-3 right-3 left-3 z-10 flex flex-wrap items-center gap-2">
        <Link href={`/app/india?city=${demoCity().id}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-line-2 bg-panel/95 px-3 py-2 text-[12.5px] whitespace-nowrap text-muted hover:border-accent/50 hover:text-accent">
          <Icon name="globe" className="h-3.5 w-3.5" /> India / {demoCity().name} / Demo ward
        </Link>
        <MapSearch onPick={(p) => select(p.parcel_id, p.bbox)} />
        <LayerControl visible={visible} onToggle={toggle} />
        <Toggle on={confidence} onClick={() => setConfidence((c) => !c)}>Confidence</Toggle>
        <Toggle on={conflictsOnly} onClick={() => setConflictsOnly((c) => !c)}>Conflicts only</Toggle>
        <Toggle on={visible.changes} onClick={() => toggle("changes")}>Changes</Toggle>
        <button onClick={() => setFit((f) => f + 1)}
          className="inline-flex items-center gap-2 rounded-lg border border-line-2 bg-panel/95 px-3 py-2 text-[13px] text-muted hover:text-text">
          <Icon name="fit" /> Fit to data
        </button>
      </div>

      <div className="absolute bottom-3 left-3 z-10 hidden sm:block"><Legend changes={visible.changes} /></div>

      {status.loading && !status.error && (
        <div className="pointer-events-none absolute inset-0 z-[5] grid place-items-center">
          <div className="w-56 space-y-2 rounded-lg border border-line bg-panel/90 p-4">
            <div className="micro">Loading harmonized parcels</div>
            <Skeleton className="h-2 w-full" /><Skeleton className="h-2 w-2/3" />
          </div>
        </div>
      )}
      {status.error && (
        <div className="absolute inset-0 z-20 grid place-items-center bg-bg/80">
          <div className="rounded-xl border border-line bg-panel">
            <ErrorState message={status.error} onRetry={() => { setStatus({ loading: true, error: null, empty: false }); setAttempt((a) => a + 1); }} />
          </div>
        </div>
      )}
      {status.empty && !status.error && (
        <div className="absolute inset-0 z-20 grid place-items-center bg-bg/70">
          <div className="rounded-xl border border-line bg-panel">
            <EmptyState title="No harmonized data yet" body="Run a harmonization to integrate the source datasets into one parcel view."
              action={<RunFirstCta />} />
          </div>
        </div>
      )}

      {selected && <ParcelDrawer parcelId={selected} onClose={() => select(null)} />}
    </div>
  );
}

export default function MapPage() {
  return (
    <Suspense fallback={<div className="p-6"><Skeleton className="h-[60vh] w-full" /></div>}>
      <MapWorkspace />
    </Suspense>
  );
}
