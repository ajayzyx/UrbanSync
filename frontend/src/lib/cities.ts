import type { BBox } from "./types";

export type CityStatus = "demo" | "validation" | "planned";

/** Mirrors the backend CityOut (spec v2 §30). */
export interface CityProfile {
  id: string;
  name: string;
  state: string;
  coordinates: [number, number]; // lon, lat
  status: CityStatus;
  dataset_type: "synthetic" | null;
  dataset_label: string | null;
  stats: {
    parcels: number | null;
    matched: number | null;
    conflicts_total: number | null;
    conflicts_pending: number | null;
    avg_confidence: number | null;
    last_run_at: string | null;
  } | null;
  test_area: { bbox: BBox; geometry: GeoJSON.Geometry } | null;
  validation: {
    city: string;
    city_name: string;
    seed: number;
    label: string;
    parcels: number;
    matched: number;
    match_precision: number | null;
    match_recall: number;
    area_conflict_recall: number;
    owner_conflict_recall: number;
    owner_false_positive_rate: number;
    generated_at: string;
  } | null;
}

const city = (
  id: string,
  name: string,
  state: string,
  lon: number,
  lat: number,
  status: CityStatus,
  dataset_label: string | null = null,
): CityProfile => ({
  id, name, state, coordinates: [lon, lat], status,
  dataset_type: null, dataset_label, stats: null, test_area: null, validation: null,
});

/** Offline fallback: names, places and statuses only — never statistics. */
export const STATIC_CITIES: CityProfile[] = [
  city("ahmedabad", "Ahmedabad", "Gujarat", 72.5714, 23.0225, "planned"),
  city("delhi", "Delhi", "Delhi", 77.209, 28.6139, "planned"),
  city("mumbai", "Mumbai", "Maharashtra", 72.8777, 19.076, "planned"),
  city("bengaluru", "Bengaluru", "Karnataka", 77.5946, 12.9716, "planned"),
  city("hyderabad", "Hyderabad", "Telangana", 78.4867, 17.385, "planned"),
  city("pune", "Pune", "Maharashtra", 73.8567, 18.5204, "demo", "Demo / Synthetic Dataset"),
  city("jaipur", "Jaipur", "Rajasthan", 75.7873, 26.9124, "planned"),
  city("surat", "Surat", "Gujarat", 72.8311, 21.1702, "validation", "Synthetic validation dataset"),
];

export const STATUS_DOT: Record<CityStatus, { color: string; label: string }> = {
  demo: { color: "#0f766e", label: "Demo dataset available" },
  validation: { color: "#0f766e", label: "Synthetic validation dataset" },
  planned: { color: "#8b94a0", label: "Dataset integration planned" },
};

export function demoCity(cities?: CityProfile[] | null): CityProfile {
  const list = cities ?? STATIC_CITIES;
  return list.find((c) => c.status === "demo") ?? STATIC_CITIES[5];
}
