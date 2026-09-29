"use client";

import Link from "next/link";
import { STATUS_DOT, type CityProfile } from "@/lib/cities";
import { fmtNum, fmtTime, pct } from "@/lib/format";
import { Icon } from "../ui/Icon";
import { useToast } from "../ui/Toast";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="micro">{label}</div>
      <div className="font-display tabular mt-0.5 text-[20px] leading-tight">{value}</div>
    </div>
  );
}

/** City information panel — numbers only ever come from the backend; planned cities get none. */
export function CityCard({ city, onExplore }: { city: CityProfile; onExplore: () => void }) {
  const toast = useToast();
  const dot = STATUS_DOT[city.status];
  const s = city.stats;
  const v = city.validation;

  return (
    <div className="space-y-4">
      <div>
        <div className="micro">{city.state}</div>
        <h2 className="font-display mt-0.5 text-[24px] font-medium">{city.name}</h2>
        <div className="mt-1.5 inline-flex items-center gap-1.5 text-[12.5px]" style={{ color: dot.color }}>
          <span className="h-2 w-2 rounded-full" style={{ background: dot.color, outline: city.status === "validation" ? `1.5px solid ${dot.color}` : undefined, outlineOffset: 1, backgroundColor: city.status === "validation" ? "#fff" : dot.color }} />
          {dot.label}
        </div>
      </div>

      {city.status === "demo" && (
        <>
          <span className="inline-block rounded-md border border-accent/40 bg-accent/[0.06] px-2 py-1 text-[11.5px] font-medium text-accent">
            {city.dataset_label ?? "Demo / Synthetic Dataset"}
          </span>
          {s ? (
            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
              <Stat label="Test parcels" value={fmtNum(s.parcels)} />
              <Stat label="Matched" value={s.matched === null ? "—" : fmtNum(s.matched)} />
              <Stat label="Conflicts pending" value={s.conflicts_pending === null ? "—" : fmtNum(s.conflicts_pending)} />
              <Stat label="Avg confidence" value={pct(s.avg_confidence, 1)} />
            </div>
          ) : (
            <p className="text-[13px] text-muted">Demo datasets are not loaded — seed the backend to explore this city.</p>
          )}
          {s && s.matched === null && (
            <p className="rounded-md border border-line bg-panel-2 px-2.5 py-2 text-[12.5px] text-muted">
              Datasets are loaded. <Link href="/app/harmonize" className="text-accent hover:underline">Run harmonization</Link> to see match statistics.
            </p>
          )}
          {s?.last_run_at && <p className="text-[11.5px] text-faint">Last harmonization {fmtTime(s.last_run_at)}</p>}
          <button onClick={onExplore}
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-[13.5px] font-medium text-white hover:bg-[#0d9488]">
            Explore area <Icon name="arrow" className="h-4 w-4" />
          </button>
          <p className="text-[11.5px] leading-relaxed text-faint">
            The current demonstration uses controlled/synthetic urban data to validate the harmonization workflow. It is not official government data.
          </p>
        </>
      )}

      {city.status === "validation" && (
        <>
          <span className="inline-block rounded-md border border-line-2 bg-panel-2 px-2 py-1 text-[11.5px] font-medium text-muted">
            Synthetic validation dataset
          </span>
          {v ? (
            <>
              <p className="text-[13px] leading-relaxed text-muted">
                The same harmonization engine — unchanged — was run against a second controlled ward generated at {city.name}
                &apos;s coordinates (seed {v.seed}) to show the model is city-agnostic.
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                <Stat label="Parcels" value={fmtNum(v.parcels)} />
                <Stat label="Match precision" value={pct(v.match_precision, 1)} />
                <Stat label="Match recall" value={pct(v.match_recall, 1)} />
                <Stat label="Area-conflict recall" value={pct(v.area_conflict_recall, 1)} />
              </div>
              <p className="text-[11.5px] text-faint">Measured against the ward&apos;s synthetic answer key, {fmtTime(v.generated_at)}.</p>
            </>
          ) : (
            <p className="text-[13px] text-muted">
              Validation report not built yet — run <code className="rounded bg-black/[0.06] px-1 font-mono text-[12px]">python -m app.validate</code>.
            </p>
          )}
        </>
      )}

      {city.status === "planned" && (
        <>
          <p className="text-[14px] font-medium">Dataset not connected yet.</p>
          <p className="text-[13px] leading-relaxed text-muted">
            UrbanSync AI is designed to support additional city datasets through the same harmonization pipeline —
            ingestion, normalization, matching, validation and review stay common while sources vary by city.
          </p>
          <div className="flex flex-wrap gap-2">
            <Link href="/#architecture"
              className="inline-flex items-center gap-1.5 rounded-lg border border-line-2 bg-panel px-3 py-2 text-[13px] hover:border-accent/60 hover:text-accent">
              View architecture
            </Link>
            <button onClick={() => toast("Noted — dataset onboarding for this city is a planned integration", "info")}
              className="inline-flex items-center gap-1.5 rounded-lg border border-line-2 bg-panel px-3 py-2 text-[13px] hover:border-accent/60 hover:text-accent">
              Request / add city dataset
            </button>
          </div>
        </>
      )}
    </div>
  );
}
