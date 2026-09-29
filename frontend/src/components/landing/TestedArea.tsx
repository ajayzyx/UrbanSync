"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { DEFAULT_VISIBLE } from "@/components/map/layers";
import { useEffect, useRef, useState } from "react";
import { useApi } from "@/lib/api";
import { fmtNum, pct } from "@/lib/format";
import type { CityProfile } from "@/lib/cities";
import { Icon } from "../ui/Icon";

const GisMap = dynamic(() => import("@/components/map/GisMap"), { ssr: false });
const LAYERS = { ...DEFAULT_VISIBLE, buildings: false, topology: false };

function Big({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-display tabular text-[30px] leading-tight font-medium">{value}</div>
      <div className="micro mt-0.5">{label}</div>
    </div>
  );
}

/** "See the system in action" — live numbers from /cities; honest placeholders otherwise. */
export function TestedArea() {
  const { data } = useApi<CityProfile[]>("/cities");
  const mapBox = useRef<HTMLDivElement>(null);
  const [showMap, setShowMap] = useState(false);
  useEffect(() => {
    // the WebGL map is heavy; mount it only when the section approaches the viewport
    const el = mapBox.current;
    if (!el) return;
    const io = new IntersectionObserver((es) => es.some((e) => e.isIntersecting) && setShowMap(true),
      { rootMargin: "400px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const demo = data?.find((c) => c.status === "demo") ?? null;
  const s = demo?.stats ?? null;

  return (
    <section className="mx-auto max-w-6xl px-4 py-20 md:px-6" id="tested-area">
      <div className="micro mb-2 text-accent">Live demonstration</div>
      <h2 className="font-display text-[30px] font-medium tracking-tight md:text-[38px]">See the system in action</h2>
      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
        <div className="space-y-6">
          <div>
            <div className="font-display text-[22px] font-medium">{demo?.name ?? "Pune"}</div>
            <div className="text-[13px] text-muted">Demo urban area · {demo?.state ?? "Maharashtra"}</div>
          </div>
          {s ? (
            <div className="grid grid-cols-2 gap-x-4 gap-y-5">
              <Big label="Test parcels" value={fmtNum(s.parcels)} />
              <Big label="Matched" value={s.matched === null ? "—" : fmtNum(s.matched)} />
              <Big label="Conflicts pending" value={s.conflicts_pending === null ? "—" : fmtNum(s.conflicts_pending)} />
              <Big label="Avg confidence" value={pct(s.avg_confidence, 1)} />
            </div>
          ) : (
            <p className="text-[13px] text-muted">
              Live statistics appear here when the backend is running — start it and run a harmonization to populate
              real numbers. Nothing on this page is hard-coded.
            </p>
          )}
          <Link href="/app/map"
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-[14px] font-medium text-white hover:bg-[#0d9488]">
            Open interactive map <Icon name="arrow" className="h-4 w-4" />
          </Link>
          <div className="rounded-xl border border-line bg-panel p-4 text-[12.5px] leading-relaxed text-muted">
            <div className="mb-1 font-medium text-text">Demo dataset</div>
            The current demonstration uses controlled/synthetic urban data to validate the harmonization workflow.
            Additional city datasets can be plugged into the same architecture.
          </div>
        </div>
        <div ref={mapBox} className="relative h-[380px] overflow-hidden rounded-xl border border-line bg-[#f2f1ec] lg:h-[460px]">
          {showMap ? <GisMap compact visible={LAYERS} /> : <div className="grid h-full place-items-center text-[12.5px] text-faint">Loading harmonized parcels…</div>}
        </div>
      </div>
    </section>
  );
}
