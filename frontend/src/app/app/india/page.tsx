"use client";

import clsx from "clsx";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { CityCard } from "@/components/india/CityCard";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/Shell";
import { ErrorState, Skeleton } from "@/components/ui/States";
import { useApi } from "@/lib/api";
import { STATIC_CITIES, STATUS_DOT, type CityProfile } from "@/lib/cities";

const IndiaMap = dynamic(() => import("@/components/india/IndiaMap"), { ssr: false });

function IndiaWorkspace() {
  const params = useSearchParams();
  const router = useRouter();
  const selected = params.get("city");
  const { data, error } = useApi<CityProfile[]>("/cities");
  const cities = data ?? STATIC_CITIES; // offline fallback carries no statistics
  const [q, setQ] = useState("");
  const [hover, setHover] = useState<string | null>(null);
  const [geo, setGeo] = useState<{ loading: boolean; error: string | null }>({ loading: true, error: null });
  const [attempt, setAttempt] = useState(0);

  const results = useMemo(() => {
    const t = q.trim().toLowerCase();
    return t ? cities.filter((c) => c.name.toLowerCase().includes(t) || c.state.toLowerCase().includes(t)) : cities;
  }, [cities, q]);
  const demoCount = cities.filter((c) => c.status === "demo").length;
  const active = cities.find((c) => c.id === (selected ?? hover)) ?? null;

  const select = (id: string | null) => router.replace(id ? `/app/india?city=${id}` : "/app/india", { scroll: false });

  return (
    <>
      <PageHeader eyebrow="India Map" title="Urban land-data harmonization across India">
        <span className="rounded-full border border-line-2 bg-panel px-3 py-1.5 text-[12.5px] text-muted">
          India · {cities.length} city profiles · {demoCount} active demo dataset{demoCount === 1 ? "" : "s"}
        </span>
      </PageHeader>
      <div className="grid grid-cols-1 gap-4 px-4 pb-8 md:px-6 lg:grid-cols-[300px_minmax(0,1fr)]">
        <div className="space-y-4">
          <div className="relative">
            <Icon name="search" className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted" />
            <input value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search a city"
              placeholder="Search a city…"
              className="w-full rounded-lg border border-line-2 bg-panel py-2 pr-3 pl-9 text-[13px] outline-none placeholder:text-faint focus:border-accent/60" />
          </div>
          <div className="overflow-hidden rounded-xl border border-line bg-panel">
            <ul className="max-h-[300px] divide-y divide-line/60 overflow-y-auto">
              {results.map((c) => (
                <li key={c.id}>
                  <button onClick={() => select(c.id)} aria-current={selected === c.id}
                    className={clsx("flex w-full items-center justify-between gap-2 px-3.5 py-2.5 text-left text-[13px] hover:bg-black/[0.02]",
                      selected === c.id && "bg-accent/[0.06]")}>
                    <span className="flex min-w-0 items-center gap-2.5">
                      <span className="h-2 w-2 shrink-0 rounded-full"
                        style={c.status === "validation"
                          ? { background: "#fff", boxShadow: `inset 0 0 0 1.5px ${STATUS_DOT[c.status].color}` }
                          : { background: STATUS_DOT[c.status].color }} />
                      <span className="truncate">{c.name}</span>
                    </span>
                    <span className="shrink-0 text-[11px] whitespace-nowrap text-faint">
                      {c.status === "planned" ? "○ Planned" : c.status === "demo" ? "● Demo" : "◐ Validation"}
                    </span>
                  </button>
                </li>
              ))}
              {results.length === 0 && (
                <li className="px-3.5 py-3 text-[12.5px] text-muted">
                  No city found — UrbanSync AI is designed to add more city datasets.
                </li>
              )}
            </ul>
          </div>
          <div className="rounded-xl border border-line bg-panel p-4">
            {active ? (
              <CityCard city={active} onExplore={() => router.push("/app/map")} />
            ) : (
              <div className="space-y-2 text-[13px] text-muted">
                <div className="micro">Select a city</div>
                <p>Hover or click a marker. The demo city carries the controlled test dataset; the rest are planned integrations.</p>
                <ul className="space-y-1 pt-1 text-[12.5px]">
                  <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-accent" /> Demo dataset available</li>
                  <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-white shadow-[inset_0_0_0_1.5px_#0f766e]" /> Synthetic validation dataset</li>
                  <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#8b94a0]" /> Dataset integration planned</li>
                </ul>
                <p className="pt-1 text-[11.5px] text-faint">More city datasets coming — the harmonization framework is common across cities.</p>
              </div>
            )}
            {error && <p className="mt-3 border-t border-line pt-2 text-[11.5px] text-[#991b1b]">Live statistics unavailable ({error.message}) — showing city registry only.</p>}
          </div>
        </div>

        <div className="relative h-[520px] overflow-hidden rounded-xl border border-line bg-panel lg:h-[calc(100dvh-190px)] lg:min-h-[560px]">
          <IndiaMap key={attempt} cities={cities} selected={selected} onSelect={select} onHover={setHover}
            onExplore={() => router.push("/app/map")} onStatus={setGeo} />
          {geo.loading && !geo.error && (
            <div className="absolute inset-0 grid place-items-center bg-panel/60">
              <Skeleton className="h-3 w-40" />
            </div>
          )}
          {geo.error && (
            <div className="absolute inset-0 grid place-items-center bg-panel/90">
              <ErrorState message={geo.error} onRetry={() => { setGeo({ loading: true, error: null }); setAttempt((a) => a + 1); }} />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default function IndiaPage() {
  return (
    <Suspense fallback={<div className="p-6"><Skeleton className="h-[70vh]" /></div>}>
      <IndiaWorkspace />
    </Suspense>
  );
}
