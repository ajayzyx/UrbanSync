"use client";

import Link from "next/link";
import { useState } from "react";
import { apiPost, useApi, type ApiError } from "@/lib/api";
import { conflictTypeLabel, fmtTime, pct, resolvableSources, SOURCE_LABELS } from "@/lib/format";
import type { ConflictOut, ParcelDetail } from "@/lib/types";
import { Icon } from "../ui/Icon";
import { Button } from "../ui/Panel";
import { ErrorState, Skeleton } from "../ui/States";
import { ConflictStatusPill } from "../ui/StatusPill";
import { useToast } from "../ui/Toast";
import { SourceCompare } from "./SourceCompare";

const VALUE_FIELDS = ["area", "owner_name", "land_use"];

export function ConflictDetail({ id, onResolved }: { id: number; onResolved: (p: ParcelDetail) => void }) {
  const { data: c, error, loading, reload } = useApi<ConflictOut>(`/conflicts/${id}`);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  if (loading && !c) return <div className="space-y-3 p-4">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-12" />)}</div>;
  if (error) return <ErrorState message={error.message} onRetry={reload} />;
  if (!c) return null;

  const isValue = c.field !== null && VALUE_FIELDS.includes(c.field);
  const pending = c.status === "Pending Review";
  const sources = isValue ? resolvableSources(c.source_values, c.field as string) : [];

  const resolve = async (body: Record<string, unknown>) => {
    setBusy(true);
    try {
      const parcel = await apiPost<ParcelDetail>(`/conflicts/${c.id}/resolve`, { ...body, note: note || undefined });
      toast(`Parcel ${c.parcel_id} updated — reviewer-resolved value recorded; source records unchanged`);
      setNote("");
      reload();
      onResolved(parcel);
    } catch (e) {
      toast((e as ApiError).message, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="micro">Conflict #{c.id} · {conflictTypeLabel(c.conflict_type)}</div>
          <div className="font-display mt-0.5 text-[20px]">{c.parcel_id}</div>
        </div>
        <div className="flex items-center gap-2">
          <ConflictStatusPill status={c.status} />
          <span className="text-[12px] text-muted">detector certainty {pct(c.confidence)}</span>
        </div>
      </div>

      <div className="rounded-lg border border-warn/30 bg-warn/[0.04] p-3">
        <div className="micro mb-1.5 text-warn">Why was this flagged?</div>
        <p className="text-[13px]">{c.explanation}</p>
        <p className="mt-2 text-[13px]"><span className="text-muted">Recommendation:</span> {c.recommended_action}</p>
      </div>

      {c.source_values && (
        <div>
          <div className="micro mb-1.5">Source values side-by-side</div>
          <SourceCompare values={c.source_values} focusField={c.field} />
        </div>
      )}

      {pending ? (
        <div className="space-y-2.5 rounded-lg border border-line bg-panel-2 p-3">
          <div className="micro">Reviewer decision</div>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional note (e.g. GNSS survey confirms)"
            className="w-full rounded-md border border-line-2 bg-panel px-2.5 py-1.5 text-[12.5px] placeholder:text-faint" />
          <div className="flex flex-wrap gap-2">
            {isValue && sources.map((s) => (
              <Button key={s} variant={s === "cadastral" ? "primary" : "ghost"} disabled={busy}
                onClick={() => resolve({ status: "Resolved", chosen_source: s, field: c.field })}>
                Use {s}
              </Button>
            ))}
            <Button disabled={busy} onClick={() => resolve({ status: "Accepted" })}>Accept as-is</Button>
            <Button disabled={busy} variant="danger" onClick={() => resolve({ status: "Ignored" })}>Ignore</Button>
          </div>
          {isValue && <p className="text-[11.5px] text-faint">The chosen value is written to the canonical parcel as reviewer-resolved. Source records are never modified.</p>}
        </div>
      ) : (
        <div className="rounded-lg border border-ok/30 bg-ok/[0.04] p-3 text-[13px]">
          {c.status} by reviewer {fmtTime(c.resolved_at)}
          {typeof c.resolution?.chosen_source === "string" && <> — used {SOURCE_LABELS[c.resolution.chosen_source]} value</>}
          {typeof c.resolution?.note === "string" && <div className="text-muted">“{c.resolution.note}”</div>}
        </div>
      )}

      <div className="flex flex-col gap-1.5 border-t border-line pt-3">
        <Link href={`/app/map?parcel=${c.parcel_id}`} className="inline-flex items-center gap-1.5 text-[13px] text-accent hover:underline">
          Open parcel <Icon name="arrow" className="h-3.5 w-3.5" />
        </Link>
        <span className="text-[11px] text-faint">{c.disclaimer}</span>
      </div>
    </div>
  );
}
