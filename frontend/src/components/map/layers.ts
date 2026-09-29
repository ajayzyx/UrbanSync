import type { LayerSpecification, StyleSpecification } from "maplibre-gl";
import { STATUS_COLORS } from "@/lib/format";

export type LayerKey = "parcels" | "roads" | "buildings" | "municipal" | "revenue" | "gnss" | "topology" | "changes";

export const LAYER_META: { key: LayerKey; label: string; hint: string }[] = [
  { key: "parcels", label: "Harmonized parcels", hint: "Canonical parcels coloured by confidence" },
  { key: "buildings", label: "Building footprints", hint: "Source: building layer" },
  { key: "municipal", label: "Municipal boundaries", hint: "Raw municipal GIS, after CRS normalization" },
  { key: "revenue", label: "Revenue records", hint: "Khasra register points" },
  { key: "gnss", label: "GNSS / GT points", hint: "Ground-truth survey control" },
  { key: "topology", label: "Topology issues", hint: "Overlaps, gaps, invalid rings" },
  { key: "changes", label: "Changes (v1 → v2)", hint: "Municipal update: new / modified / removed" },
  { key: "roads", label: "Roads", hint: "Context" },
];

export const DEFAULT_VISIBLE: Record<LayerKey, boolean> = {
  parcels: true,
  roads: true,
  buildings: true,
  municipal: false,
  revenue: false,
  gnss: false,
  topology: true,
  changes: false,
};

export const BASE_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "background", type: "background", paint: { "background-color": "#f2f1ec" } }],
};

const statusMatch = [
  "match",
  ["get", "match_status"],
  "HARMONIZED", STATUS_COLORS.HARMONIZED,
  "REVIEW", STATUS_COLORS.REVIEW,
  "CONFLICT", STATUS_COLORS.CONFLICT,
  STATUS_COLORS.UNMATCHED,
] as unknown as string;

/** Map layers per data layer, in draw order. */
export const MAP_LAYERS: Record<LayerKey, LayerSpecification[]> = {
  roads: [{ id: "roads", type: "line", source: "roads", paint: { "line-color": "#e3e1d8", "line-width": ["interpolate", ["linear"], ["zoom"], 14, 3, 18, 26] } }],
  parcels: [
    { id: "parcels-fill", type: "fill", source: "parcels", paint: { "fill-color": statusMatch, "fill-opacity": 0.25 } },
    { id: "parcels-line", type: "line", source: "parcels", paint: { "line-color": statusMatch, "line-width": 0.8, "line-opacity": 0.9 } },
  ],
  buildings: [{ id: "buildings", type: "fill", source: "buildings", paint: { "fill-color": "#b6bcc4", "fill-opacity": 0.35 } }],
  municipal: [{ id: "municipal", type: "line", source: "municipal", paint: { "line-color": "#0f766e", "line-width": 1, "line-dasharray": [2, 2] } }],
  revenue: [{ id: "revenue", type: "circle", source: "revenue", paint: { "circle-radius": 2.6, "circle-color": "#334155", "circle-stroke-color": "#ffffff", "circle-stroke-width": 0.9 } }],
  gnss: [{ id: "gnss", type: "circle", source: "gnss", paint: { "circle-radius": 3.2, "circle-color": "#0f766e", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1 } }],
  topology: [
    { id: "topology-fill", type: "fill", source: "topology", paint: { "fill-color": "#b91c1c", "fill-opacity": 0.4 } },
    { id: "topology-line", type: "line", source: "topology", paint: { "line-color": "#b91c1c", "line-width": 1.4 } },
  ],
  changes: [{
    id: "changes", type: "line", source: "changes",
    filter: ["!=", ["get", "change"], "UNCHANGED"],
    paint: {
      "line-color": ["match", ["get", "change"], "NEW", "#15803d", "MODIFIED", "#b45309", "REMOVED", "#b91c1c", "#64748b"] as unknown as string,
      "line-width": 2,
    },
  }],
};

export const DRAW_ORDER: LayerKey[] = ["roads", "parcels", "buildings", "municipal", "changes", "topology", "revenue", "gnss"];
