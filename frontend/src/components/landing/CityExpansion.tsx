"use client";

import Link from "next/link";
import { useApi } from "@/lib/api";
import { STATIC_CITIES, STATUS_DOT, type CityProfile } from "@/lib/cities";
import { pct } from "@/lib/format";

const PIPELINE = ["CITY DATASET", "SOURCE CONNECTORS", "NORMALIZATION", "URBANSYNC AI ENGINE", "CITY HARMONIZED LAYER"];

export function CityExpansion() {
  const { data } = useApi<CityProfile[]>("/cities");
  const cities = data ?? STATIC_CITIES;
  const surat = cities.find((c) => c.status === "validation");

  return (
    <section className="border-t border-line bg-panel-2/60" id="architecture">
      <div className="mx-auto max-w-6xl px-4 py-20 md:px-6">
        <div className="micro mb-2 text-accent">Multi-city architecture</div>
        <h2 className="font-display max-w-2xl text-[30px] leading-tight font-medium tracking-tight md:text-[38px]">
          Expanding Across India&apos;s Cities
        </h2>
        <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-muted">
          UrbanSync AI is designed to work city-by-city, with a common harmonization framework that can ingest datasets
          from different urban authorities and survey systems. <strong className="text-text">More city datasets are
          needed to expand UrbanSync AI across India</strong> — the current MVP validates the workflow on a controlled
          dataset, and each new city plugs into the same spatial intelligence layer.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-2">
          <div>
            <div className="micro mb-3">City coverage · more city datasets coming</div>
            <ul className="divide-y divide-line/60 overflow-hidden rounded-xl border border-line bg-panel">
              {cities.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-3 px-4 py-2.5 text-[13.5px]">
                  <span className="flex items-center gap-2.5">
                    <span className="h-2 w-2 rounded-full"
                      style={c.status === "validation"
                        ? { background: "#fff", boxShadow: `inset 0 0 0 1.5px ${STATUS_DOT[c.status].color}` }
                        : { background: STATUS_DOT[c.status].color }} />
                    {c.name}
                  </span>
                  <span className={`text-[12px] ${c.status === "planned" ? "text-faint" : "text-accent"}`}>
                    {c.status === "demo" ? "● Demo dataset available" : c.status === "validation" ? "◐ Synthetic validation dataset" : "○ Dataset integration planned"}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-6">
            <div>
              <div className="micro mb-3">Built for more cities, not just one test area</div>
              <p className="text-[13.5px] leading-relaxed text-muted">
                The architecture is designed to accept additional city-specific datasets and source systems without
                changing the core spatial intelligence workflow.
              </p>
              <ol className="mt-4 space-y-1">
                {PIPELINE.map((p, i) => (
                  <li key={p} className="font-mono text-[12px] tracking-[0.1em]">
                    {i > 0 && <span className="text-faint">↓ </span>}
                    <span className={i === 3 ? "font-semibold text-accent" : "text-muted"}>{p}</span>
                  </li>
                ))}
              </ol>
            </div>
            <div className="rounded-xl border border-line bg-panel p-5">
              <div className="micro mb-2">Designed to generalize across cities</div>
              {surat?.validation ? (
                <p className="text-[13.5px] leading-relaxed text-muted">
                  The unchanged engine was re-run on a second controlled ward at <strong className="text-text">{surat.name}</strong>
                  {" "}(synthetic validation dataset, seed {surat.validation.seed}): {" "}
                  <span className="tabular font-medium text-accent">{pct(surat.validation.match_precision, 1)}</span> match precision,{" "}
                  <span className="tabular font-medium text-accent">{pct(surat.validation.match_recall, 1)}</span> recall and{" "}
                  <span className="tabular font-medium text-accent">{pct(surat.validation.area_conflict_recall, 1)}</span> area-conflict
                  recall against its answer key. The intelligence layer stays common while source datasets vary by city.
                </p>
              ) : (
                <p className="text-[13.5px] leading-relaxed text-muted">
                  The same engine can be re-run on a second controlled city dataset ({surat?.name ?? "Surat"}, synthetic
                  validation dataset) to demonstrate the model is city-agnostic — start the backend to see the measured
                  results here.
                </p>
              )}
              <Link href="/app/india?city=surat" className="mt-3 inline-block text-[13px] text-accent hover:underline">
                View on the India map →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
