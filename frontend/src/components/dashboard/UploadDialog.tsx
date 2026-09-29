"use client";

import { useState } from "react";
import { apiUpload, type ApiError } from "@/lib/api";
import { SOURCE_LABELS } from "@/lib/format";
import type { Dataset } from "@/lib/types";
import { Icon } from "../ui/Icon";
import { Button } from "../ui/Panel";

const TYPES = ["cadastral", "municipal", "revenue", "buildings", "gnss", "roads"];

export function UploadDialog({ onClose, onUploaded }: { onClose: () => void; onUploaded: (d: Dataset) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState("buildings");
  const [crs, setCrs] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      onUploaded(await apiUpload<Dataset>(file, type, crs.trim() || undefined));
    } catch (err) {
      setError((err as ApiError).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label="Upload dataset">
      <form onSubmit={submit} className="w-full max-w-md rounded-xl border border-line-2 bg-panel p-5 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-[17px]">Upload dataset</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="text-muted hover:text-text"><Icon name="x" /></button>
        </div>
        <label className="micro mb-1 block" htmlFor="up-file">File (.geojson, .json, .csv, .zip)</label>
        <input id="up-file" type="file" accept=".geojson,.json,.csv,.zip"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="mb-4 block w-full text-[13px] text-muted file:mr-3 file:rounded-md file:border file:border-line-2 file:bg-panel-2 file:px-3 file:py-1.5 file:text-text" />
        <div className="mb-4 grid grid-cols-2 gap-3">
          <div>
            <label className="micro mb-1 block" htmlFor="up-type">Source type</label>
            <select id="up-type" value={type} onChange={(e) => setType(e.target.value)}
              className="w-full rounded-lg border border-line-2 bg-panel-2 px-2.5 py-2 text-[13px]">
              {TYPES.map((t) => <option key={t} value={t}>{SOURCE_LABELS[t]}</option>)}
            </select>
          </div>
          <div>
            <label className="micro mb-1 block" htmlFor="up-crs">CRS (optional)</label>
            <input id="up-crs" value={crs} onChange={(e) => setCrs(e.target.value)} placeholder="auto-detect"
              className="w-full rounded-lg border border-line-2 bg-panel-2 px-2.5 py-2 text-[13px] placeholder:text-faint" />
          </div>
        </div>
        {error && <p role="alert" className="mb-3 rounded-md border border-bad/40 bg-bad/10 px-3 py-2 text-[12.5px] text-[#991b1b]">{error}</p>}
        <p className="mb-4 text-[11.5px] text-faint">Files are parsed, never executed. CRS is detected from the file; CSVs need latitude/longitude columns.</p>
        <div className="flex justify-end gap-2">
          <Button type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={!file || busy}>
            <Icon name="upload" className="h-3.5 w-3.5" /> {busy ? "Uploading…" : "Upload & ingest"}
          </Button>
        </div>
      </form>
    </div>
  );
}
