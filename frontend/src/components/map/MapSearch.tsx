"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { pct, statusColor } from "@/lib/format";
import type { ParcelSummary } from "@/lib/types";
import { Icon } from "../ui/Icon";

export function MapSearch({ onPick }: { onPick: (p: ParcelSummary) => void }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<ParcelSummary[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (q.trim().length < 2) return;
    const t = setTimeout(() => {
      apiGet<ParcelSummary[]>(`/parcels?q=${encodeURIComponent(q.trim())}&limit=8`).then((r) => {
        setResults(r);
        setOpen(true);
      }).catch(() => setResults([]));
    }, 200);
    return () => clearTimeout(t);
  }, [q]);

  const pick = (p: ParcelSummary) => {
    onPick(p);
    setOpen(false);
    setQ(p.parcel_id);
  };

  return (
    <div className="relative w-full sm:w-72">
      <Icon name="search" className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted" />
      <input
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          if (e.target.value.trim().length < 2) setOpen(false);
        }}
        onKeyDown={(e) => e.key === "Enter" && results[0] && pick(results[0])}
        onFocus={() => results.length && setOpen(true)}
        placeholder="Search parcel, owner, Khasra, property…"
        aria-label="Search parcels"
        className="w-full rounded-lg border border-line-2 bg-panel/95 py-2 pr-3 pl-9 text-[13px] outline-none placeholder:text-faint focus:border-accent/60"
      />
      {open && (
        <ul className="absolute top-full right-0 left-0 z-20 mt-1 overflow-hidden rounded-lg border border-line-2 bg-panel shadow-xl shadow-black/10">
          {results.length === 0 && <li className="px-3 py-2 text-[12.5px] text-muted">No parcels found</li>}
          {results.map((r) => (
            <li key={r.parcel_id}>
              <button onClick={() => pick(r)} className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-[12.5px] hover:bg-black/[0.03]">
                <span><span className="font-mono">{r.parcel_id}</span> <span className="text-muted">· {r.owner_name ?? "—"}</span></span>
                <span className="tabular" style={{ color: statusColor(r.match_status) }}>{pct(r.confidence_score)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
