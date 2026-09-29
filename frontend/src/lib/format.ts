import type { ConflictType, MatchClass, MatchStatus, SourceValues } from "./types";

export const STATUS_COLORS: Record<MatchStatus, string> = {
  HARMONIZED: "#15803d",
  REVIEW: "#b45309",
  CONFLICT: "#b91c1c",
  UNMATCHED: "#64748b",
};

const CLASS_TO_STATUS: Record<MatchClass, MatchStatus> = { HIGH: "HARMONIZED", REVIEW: "REVIEW", CONFLICT: "CONFLICT" };

export function statusColor(s: MatchStatus | MatchClass): string {
  return STATUS_COLORS[(CLASS_TO_STATUS as Record<string, MatchStatus>)[s] ?? (s as MatchStatus)] ?? "#64748b";
}

export function pct(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return `${(x * 100).toFixed(digits)}%`;
}

const CLASS_LABELS: Record<string, string> = {
  HIGH: "High confidence",
  HARMONIZED: "High confidence",
  REVIEW: "Review",
  CONFLICT: "Conflict",
  UNMATCHED: "Unmatched",
};

export function classLabel(c: MatchStatus | MatchClass): string {
  return CLASS_LABELS[c] ?? c;
}

const CONFLICT_LABELS: Record<ConflictType, string> = {
  AREA_MISMATCH: "Area mismatch",
  OWNER_MISMATCH: "Owner mismatch",
  DUPLICATE: "Duplicate",
  BOUNDARY_OVERLAP: "Boundary overlap",
  MISSING_ATTRIBUTE: "Missing attribute",
  SPATIAL_MISMATCH: "Spatial mismatch",
  TOPOLOGY: "Topology",
};

export function conflictTypeLabel(t: ConflictType | string): string {
  return CONFLICT_LABELS[t as ConflictType] ?? t;
}

export function fmtArea(m2: number | null | undefined): string {
  if (m2 === null || m2 === undefined) return "—";
  return `${Math.round(m2).toLocaleString("en-IN")} m²`;
}

export function fmtNum(n: number | null | undefined): string {
  return n === null || n === undefined ? "—" : n.toLocaleString("en-IN");
}

export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

export function fmtValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") return Number.isInteger(v) ? v.toLocaleString("en-IN") : v.toFixed(1);
  return String(v);
}

export const SOURCE_LABELS: Record<string, string> = {
  cadastral: "Cadastral",
  municipal: "Municipal GIS",
  revenue: "Revenue",
  buildings: "Building footprints",
  gnss: "GNSS / GT",
  roads: "Roads",
  drone_ori: "Drone / ORI",
  dsm_dtm: "DSM / DTM",
  utilities: "Utilities",
};

/** HARMONIZED with a non-HIGH match only happens when a reviewer confirmed the parcel. */
export function parcelStatusLabel(status: MatchStatus, primaryMatchClasses: string[]): string {
  if (status === "HARMONIZED" && primaryMatchClasses.some((c) => c !== "HIGH")) return "Reviewer-confirmed";
  return classLabel(status);
}

export function resolvableSources(values: SourceValues | undefined, field: string): string[] {
  return ["cadastral", "municipal", "revenue"].filter((s) => {
    const v = values?.[s]?.[field];
    return v !== null && v !== undefined && v !== "";
  });
}
