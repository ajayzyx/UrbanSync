export type MatchStatus = "HARMONIZED" | "REVIEW" | "CONFLICT" | "UNMATCHED";
export type MatchClass = "HIGH" | "REVIEW" | "CONFLICT";
export type ConflictStatus = "Pending Review" | "Accepted" | "Resolved" | "Ignored";
export type ConflictType =
  | "AREA_MISMATCH"
  | "OWNER_MISMATCH"
  | "DUPLICATE"
  | "BOUNDARY_OVERLAP"
  | "MISSING_ATTRIBUTE"
  | "SPATIAL_MISMATCH"
  | "TOPOLOGY";
export type BBox = [number, number, number, number];

export interface Dataset {
  id: number;
  name: string;
  source_type: string;
  version: number;
  file_name: string | null;
  record_count: number;
  source_crs: string | null;
  target_crs: string;
  status: "registered" | "ingested" | "processed" | "error";
  last_processed: string | null;
  fields: string[];
  metadata: Record<string, unknown>;
}

export interface Stage {
  key: string;
  label: string;
  status: "pending" | "running" | "done" | "failed";
  started_at: string | null;
  finished_at: string | null;
  detail: string | null;
}

export interface RunSummary {
  datasets?: number;
  features?: number;
  parcels?: number;
  matched?: number;
  revenue_matched?: number;
  high?: number;
  review?: number;
  conflict_class?: number;
  unmatched?: number;
  conflicts?: number;
  topology_issues?: number;
  avg_confidence?: number | null;
  crs_transforms?: { dataset: string; from: string; to: string }[];
  changes?: Record<string, number>;
  duration_s?: number;
}

export interface Run {
  id: number;
  status: "running" | "completed" | "failed";
  stages: Stage[];
  summary: RunSummary;
  started_at: string;
  finished_at: string | null;
  error: string | null;
}

export interface ParcelSummary {
  parcel_id: string;
  owner_name: string | null;
  area: number | null;
  land_use: string | null;
  confidence_score: number | null;
  match_status: MatchStatus;
  topology_status: "VALID" | "ISSUE" | "SUGGESTED_FIX";
  source_count: number;
  conflict_count: number;
  bbox: BBox;
}

export type Components = Record<"geometry" | "centroid" | "area" | "shape" | "attribute" | "temporal", number | null>;

export interface MatchOut {
  id: number;
  source_type: string;
  record_id: string;
  components: Components;
  final_confidence: number;
  match_class: MatchClass;
  evidence: Record<string, unknown>;
  explanation: string;
  is_duplicate: boolean;
}

export interface Provenance {
  source_type: string;
  label: string;
  dataset_id: number;
  dataset_name: string;
  source_feature_id: number;
  record_id: string;
}

export interface ResolvedValue {
  value: unknown;
  source: string;
  resolved_by: string;
  resolved_at: string;
  note: string | null;
}

export type SourceValues = Record<string, Record<string, string | number | null>>;

export interface ConflictOut {
  id: number;
  parcel_id: string;
  conflict_type: ConflictType;
  source_a: string;
  source_b: string;
  field: string | null;
  observed: { a?: unknown; b?: unknown; delta?: string };
  confidence: number;
  explanation: string;
  recommended_action: string;
  status: ConflictStatus;
  resolution: Record<string, unknown> | null;
  resolved_at: string | null;
  source_values?: SourceValues;
  bbox?: BBox;
  disclaimer?: string;
}

export interface ParcelDetail extends ParcelSummary {
  geometry: GeoJSON.Geometry;
  provenance: Provenance[];
  matches: MatchOut[];
  source_values: SourceValues;
  conflicts: ConflictOut[];
  topology: { issue_type: string; detail: string; fix_status: string }[];
  resolved_values: Record<string, ResolvedValue>;
  building_count: number;
  gnss_count: number;
  last_updated: string | null;
  disclaimer: string;
}

export interface Analytics {
  kpis: {
    datasets: number;
    parcels: number;
    matched: number;
    high: number;
    review: number;
    conflict_class: number;
    unmatched: number;
    conflicts_total: number;
    conflicts_pending: number;
    conflicts_resolved: number;
    topology_issues: number;
    avg_confidence: number | null;
    last_run_at: string | null;
  };
  match_distribution: { class: MatchStatus; count: number }[];
  confidence_histogram: { bin: string; count: number }[];
  conflict_breakdown: { type: ConflictType; count: number }[];
  topology_stats: { type: string; count: number }[];
  quality_before_after: { metric: string; before: number | null; after: number | null }[];
  evaluation: {
    label: string;
    match_precision: number | null;
    match_recall: number;
    area_conflict_recall: number;
    owner_conflict_recall: number;
    owner_false_positive_rate: number;
    ml_match_precision: number | null;
    ml_baseline_agreement: number | null;
  } | null;
  run: Run | null;
}

export interface Mapping {
  dataset: string;
  source_type: string;
  source_field: string;
  canonical_field: string | null;
  confidence: number;
  method: string;
}
