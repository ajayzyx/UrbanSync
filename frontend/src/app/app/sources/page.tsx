"use client";

import { useState } from "react";
import { DatasetTable } from "@/components/dashboard/DatasetTable";
import { UploadDialog } from "@/components/dashboard/UploadDialog";
import { Icon } from "@/components/ui/Icon";
import { Button, Panel } from "@/components/ui/Panel";
import { PageHeader } from "@/components/ui/Shell";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { useToast } from "@/components/ui/Toast";
import { useApi } from "@/lib/api";
import { demoCity } from "@/lib/cities";
import type { Dataset } from "@/lib/types";

export default function SourcesPage() {
  const { data, error, loading, reload } = useApi<Dataset[]>("/datasets");
  const [upload, setUpload] = useState(false);
  const toast = useToast();
  const vector = data?.filter((d) => d.status !== "registered") ?? [];
  const crsCount = new Set(vector.map((d) => d.source_crs)).size;

  return (
    <>
      <PageHeader eyebrow="Integrate" title="Data Sources">
        <span className="rounded-md border border-accent/40 bg-accent/[0.06] px-2.5 py-1.5 text-[12px] font-medium text-accent">
          {demoCity().name} · Demo / Synthetic Dataset
        </span>
        <Button variant="primary" onClick={() => setUpload(true)}><Icon name="upload" className="h-3.5 w-3.5" /> Upload dataset</Button>
      </PageHeader>
      <div className="space-y-4 px-4 pb-8 md:px-6">
        {data && data.length > 0 && (
          <p className="text-[13px] text-muted">
            {vector.length} vector datasets in {crsCount} coordinate reference systems, plus {data.length - vector.length} registered
            imagery/elevation/utility sources. Everything is normalized to <span className="font-mono text-accent">EPSG:32643</span> (UTM 43N) during harmonization.
          </p>
        )}
        <Panel bodyClassName="p-0 px-4">
          {loading && !data && <div className="space-y-2 py-4">{[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-9" />)}</div>}
          {error && <ErrorState message={error.message} onRetry={reload} />}
          {data && data.length === 0 && (
            <EmptyState title="No datasets loaded" body={<>Seed the demo ward with <code className="font-mono">uv run python -m app.seed</code> or upload a file.</>} />
          )}
          {data && data.length > 0 && <DatasetTable datasets={data} />}
        </Panel>
      </div>
      {upload && (
        <UploadDialog onClose={() => setUpload(false)} onUploaded={(d) => {
          setUpload(false);
          toast(`Ingested ${d.record_count.toLocaleString("en-IN")} records from ${d.file_name} (${d.source_crs} → ${d.target_crs})`);
          reload();
        }} />
      )}
    </>
  );
}
