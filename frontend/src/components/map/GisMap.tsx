"use client";

import { Map as MlMap, NavigationControl, setWorkerUrl, type FilterSpecification, type GeoJSONSource, type LngLatBoundsLike, type MapLayerMouseEvent } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import type { BBox } from "@/lib/types";
import { BASE_STYLE, DRAW_ORDER, MAP_LAYERS, type LayerKey } from "./layers";

export interface GisMapProps {
  visible: Record<LayerKey, boolean>;
  colorByConfidence?: boolean;
  conflictsOnly?: boolean;
  selectedParcel?: string | null;
  onSelect?: (parcelId: string) => void;
  focusBbox?: BBox | null;
  fitSignal?: number;
  dataVersion?: number;
  compact?: boolean;
  onStatus?: (s: { loading: boolean; error: string | null; empty: boolean }) => void;
}

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const PAD = { top: 60, bottom: 60, left: 60, right: 60 };

function bboxOf(fc: GeoJSON.FeatureCollection): BBox | null {
  let minx = Infinity, miny = Infinity, maxx = -Infinity, maxy = -Infinity;
  const walk = (c: unknown): void => {
    if (Array.isArray(c) && typeof c[0] === "number") {
      const [x, y] = c as number[];
      minx = Math.min(minx, x); miny = Math.min(miny, y); maxx = Math.max(maxx, x); maxy = Math.max(maxy, y);
    } else if (Array.isArray(c)) c.forEach(walk);
  };
  fc.features.forEach((f) => f.geometry && "coordinates" in f.geometry && walk(f.geometry.coordinates));
  return Number.isFinite(minx) ? [minx, miny, maxx, maxy] : null;
}

async function fetchLayer(key: LayerKey): Promise<GeoJSON.FeatureCollection> {
  const res = await fetch(`${API_URL}/layers/${key}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Layer ${key}: ${res.status}`);
  return res.json();
}

export default function GisMap({
  visible, colorByConfidence = true, conflictsOnly = false, selectedParcel, onSelect, focusBbox,
  fitSignal = 0, dataVersion = 0, compact = false, onStatus,
}: GisMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const loaded = useRef<Set<LayerKey>>(new Set());
  const extent = useRef<BBox | null>(null);
  const [ready, setReady] = useState(false);
  const [layersVersion, setLayersVersion] = useState(0);
  const focusRef = useRef<BBox | null>(focusBbox ?? null);
  const onSelectRef = useRef(onSelect);
  const onStatusRef = useRef(onStatus);
  useEffect(() => {
    onSelectRef.current = onSelect;
    focusRef.current = focusBbox ?? null;
    onStatusRef.current = onStatus;
  });

  // init once
  useEffect(() => {
    if (!container.current) return;
    const map = new MlMap({
      container: container.current, style: BASE_STYLE, center: [73.875, 18.531], zoom: 15,
      attributionControl: false, dragRotate: false, pitchWithRotate: false, interactive: true,
    });
    mapRef.current = map;
    (window as unknown as { __urbansyncMap?: MlMap }).__urbansyncMap = map; // handle for e2e checks
    if (!compact) map.addControl(new NavigationControl({ showCompass: false }), "bottom-right");
    map.on("load", () => setReady(true));
    const ro = new ResizeObserver(() => map.resize()); // keep the canvas matched to its (grid/flex) container
    ro.observe(container.current);
    map.on("click", "parcels-fill", (e: MapLayerMouseEvent) => {
      const id = e.features?.[0]?.properties?.parcel_id;
      if (id) onSelectRef.current?.(String(id));
    });
    map.on("mouseenter", "parcels-fill", () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", "parcels-fill", () => (map.getCanvas().style.cursor = ""));
    return () => {
      ro.disconnect();
      map.remove();
      mapRef.current = null;
      loaded.current = new Set();
    };
  }, [compact]);

  // load visible layers lazily (parcels always)
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const wanted = DRAW_ORDER.filter((k) => (k === "parcels" || visible[k]) && !loaded.current.has(k));
    if (!wanted.length) return;
    wanted.forEach((k) => loaded.current.add(k));
    if (wanted.includes("parcels")) onStatusRef.current?.({ loading: true, error: null, empty: false });
    Promise.all(wanted.map((k) => fetchLayer(k).then((fc) => [k, fc] as const)))
      .then((pairs) => {
        for (const [k, fc] of pairs) {
          map.addSource(k, { type: "geojson", data: fc, promoteId: k === "parcels" ? "parcel_id" : undefined });
          for (const layer of MAP_LAYERS[k]) {
            const before = DRAW_ORDER.slice(DRAW_ORDER.indexOf(k) + 1)
              .flatMap((n) => MAP_LAYERS[n].map((l) => l.id)).find((id) => map.getLayer(id));
            map.addLayer(layer, before);
          }
          if (k === "parcels") {
            map.addLayer({ id: "parcels-selected", type: "line", source: "parcels", filter: ["==", ["get", "parcel_id"], ""],
              paint: { "line-color": "#0f766e", "line-width": 2.8 } });
            extent.current = bboxOf(fc);
            const target = focusRef.current ?? extent.current; // a pending focus wins over the initial fit
            if (target) map.fitBounds(target as LngLatBoundsLike, { padding: compact ? 20 : PAD, maxZoom: compact ? 18 : 19, duration: 0 });
            onStatusRef.current?.({ loading: false, error: null, empty: fc.features.length === 0 });
          }
        }
        setLayersVersion((v) => v + 1); // re-render so the style effect applies current props
      })
      .catch((e: Error) => {
        wanted.forEach((k) => loaded.current.delete(k));
        onStatusRef.current?.({ loading: false, error: e.message.includes("fetch") ? `Backend unreachable at ${API_URL}` : e.message, empty: false });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, visible]);

  function applyStyleState() {
    const map = mapRef.current;
    if (!map) return;
    for (const k of DRAW_ORDER) {
      for (const l of MAP_LAYERS[k]) {
        if (map.getLayer(l.id)) map.setLayoutProperty(l.id, "visibility", k === "parcels" || visible[k] ? "visible" : "none");
      }
    }
    if (map.getLayer("parcels-fill")) {
      const f = conflictsOnly ? ["in", ["get", "match_status"], ["literal", ["REVIEW", "CONFLICT"]]] : null;
      map.setFilter("parcels-fill", f as FilterSpecification | null);
      map.setFilter("parcels-line", f as FilterSpecification | null);
      map.setPaintProperty("parcels-fill", "fill-opacity", colorByConfidence ? 0.25 : 0.08);
      map.setPaintProperty("parcels-line", "line-color", colorByConfidence
        ? (MAP_LAYERS.parcels[1].paint as Record<string, unknown>)["line-color"] as string : "#8b94a0");
      map.setPaintProperty("parcels-fill", "fill-color", colorByConfidence
        ? (MAP_LAYERS.parcels[0].paint as Record<string, unknown>)["fill-color"] as string : "#8b94a0");
    }
    if (map.getLayer("parcels-selected")) map.setFilter("parcels-selected", ["==", ["get", "parcel_id"], selectedParcel ?? ""]);
  }

  // style state is applied imperatively (the map itself never re-renders)
  useEffect(applyStyleState, [layersVersion, visible, conflictsOnly, colorByConfidence, selectedParcel]);

  // fly to focus
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !focusBbox) return;
    map.fitBounds(focusBbox as LngLatBoundsLike, { padding: compact ? 20 : { ...PAD, right: 440 }, maxZoom: compact ? 18 : 19, duration: 700 });
  }, [ready, focusBbox, compact]);

  // fit to data
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !fitSignal || !extent.current) return;
    map.fitBounds(extent.current as LngLatBoundsLike, { padding: PAD, duration: 600 });
  }, [ready, fitSignal]);

  // refresh parcel data after a resolution
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !dataVersion) return;
    fetchLayer("parcels").then((fc) => (map.getSource("parcels") as GeoJSONSource | undefined)?.setData(fc)).catch(() => {});
  }, [ready, dataVersion]);

  // maplibre sets position:relative on its container, so size it from an absolutely positioned wrapper
  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" data-testid="gis-map" />
    </div>
  );
}
