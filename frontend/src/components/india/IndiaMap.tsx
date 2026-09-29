"use client";

import clsx from "clsx";
import {
  Map as MlMap,
  Marker,
  NavigationControl,
  setWorkerUrl,
  type GeoJSONSource,
  type LngLatBoundsLike,
  type StyleSpecification,
} from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import type { CityProfile } from "@/lib/cities";
import { Icon } from "../ui/Icon";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

export const INDIA_BOUNDS: LngLatBoundsLike = [
  [68, 6.5],
  [97.5, 37.5],
];

const STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "background", type: "background", paint: { "background-color": "#eef1f2" } }],
};

export interface IndiaMapProps {
  cities: CityProfile[];
  selected: string | null;
  onSelect: (id: string | null) => void;
  onHover?: (id: string | null) => void;
  onExplore?: () => void;
  onStatus?: (s: { loading: boolean; error: string | null }) => void;
  compact?: boolean;
}

/** Interactive India map: vendored state boundaries, DOM city markers (no tile/glyph servers). */
export default function IndiaMap({ cities, selected, onSelect, onHover, onExplore, onStatus, compact = false }: IndiaMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const markers = useRef<Map<string, Marker>>(new Map());
  const [ready, setReady] = useState(false);
  const parcelsLoaded = useRef(false);
  const cbs = useRef({ onSelect, onHover, onExplore, onStatus });
  useEffect(() => {
    cbs.current = { onSelect, onHover, onExplore, onStatus };
  });

  // init map + states layer
  useEffect(() => {
    if (!container.current) return;
    const map = new MlMap({
      container: container.current, style: STYLE, bounds: INDIA_BOUNDS,
      fitBoundsOptions: { padding: compact ? 8 : 24 }, attributionControl: false,
      dragRotate: false, pitchWithRotate: false,
    });
    mapRef.current = map;
    (window as unknown as { __indiaMap?: MlMap }).__indiaMap = map;
    if (!compact) map.addControl(new NavigationControl({ showCompass: false }), "bottom-right");
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(container.current);

    cbs.current.onStatus?.({ loading: true, error: null });
    map.on("load", async () => {
      try {
        const res = await fetch("/geo/india-states.json");
        if (!res.ok) throw new Error(`India boundaries failed to load (${res.status})`);
        const fc = (await res.json()) as GeoJSON.FeatureCollection;
        if (!fc.features?.length) throw new Error("India boundaries file is empty");
        map.addSource("states", { type: "geojson", data: fc });
        map.addLayer({ id: "states-fill", type: "fill", source: "states", paint: { "fill-color": "#f8f7f3" } });
        map.addLayer({ id: "states-line", type: "line", source: "states",
          paint: { "line-color": "#cfccc0", "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.5, 8, 1.2] } });
        map.addLayer({ id: "test-area-fill", type: "fill", source: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
          paint: { "fill-color": "#0f766e", "fill-opacity": 0.1 } });
        map.addLayer({ id: "test-area-line", type: "line", source: "test-area-fill",
          paint: { "line-color": "#0f766e", "line-width": 1.5 } });
        map.addSource("demo-parcels", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        const statusColor = ["match", ["get", "match_status"], "HARMONIZED", "#15803d", "REVIEW", "#b45309",
          "CONFLICT", "#b91c1c", "#64748b"] as unknown as string;
        map.addLayer({ id: "demo-parcels-fill", type: "fill", source: "demo-parcels", minzoom: 11,
          paint: { "fill-color": statusColor, "fill-opacity": 0.22 } });
        map.addLayer({ id: "demo-parcels-line", type: "line", source: "demo-parcels", minzoom: 11,
          paint: { "line-color": statusColor, "line-width": 0.6, "line-opacity": 0.8 } });
        setReady(true);
        cbs.current.onStatus?.({ loading: false, error: null });
      } catch (e) {
        cbs.current.onStatus?.({ loading: false, error: (e as Error).message });
      }
    });
    return () => {
      ro.disconnect();
      markers.current.forEach((m) => m.remove());
      markers.current = new Map();
      map.remove();
      mapRef.current = null;
    };
     
  }, [compact]);

  // city markers (DOM => accessible buttons, no glyph server needed)
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    markers.current.forEach((m) => m.remove());
    markers.current = new Map();
    for (const c of cities) {
      const el = document.createElement("button");
      el.type = "button";
      el.setAttribute("aria-label", c.name);
      el.className = "india-marker";
      el.dataset.status = c.status;
      el.innerHTML =
        `<span class="dot${c.status === "demo" ? " dot-pulse" : ""}"></span>` +
        `<span class="label">${c.name}</span>`;
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        cbs.current.onSelect?.(c.id);
      });
      el.addEventListener("mouseenter", () => cbs.current.onHover?.(c.id));
      el.addEventListener("mouseleave", () => cbs.current.onHover?.(null));
      const m = new Marker({ element: el, anchor: "left", offset: [-5, 0] }).setLngLat(c.coordinates).addTo(map);
      markers.current.set(c.id, m);
    }
  }, [ready, cities]);

  // selection: fly + test-area highlight
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    markers.current.forEach((m, id) => m.getElement().classList.toggle("selected", id === selected));
    const city = cities.find((c) => c.id === selected);
    const src = map.getSource("test-area-fill") as GeoJSONSource | undefined;
    if (!city) {
      src?.setData({ type: "FeatureCollection", features: [] });
      map.fitBounds(INDIA_BOUNDS, { padding: compact ? 8 : 24, duration: 700 });
      return;
    }
    if (city.status === "demo" && city.test_area) {
      src?.setData({ type: "Feature", properties: {}, geometry: city.test_area.geometry });
      if (!parcelsLoaded.current) {
        parcelsLoaded.current = true;
        fetch(`${API_URL}/layers/parcels`).then((r) => (r.ok ? r.json() : null))
          .then((fc: GeoJSON.FeatureCollection | null) => {
            if (fc?.features?.length) (map.getSource("demo-parcels") as GeoJSONSource | undefined)?.setData(fc);
            else parcelsLoaded.current = false; // nothing harmonized yet — retry on the next selection
          })
          .catch(() => { parcelsLoaded.current = false; });
      }
      const [minx, miny, maxx, maxy] = city.test_area.bbox;
      // frame the ward with breathing room so the highlight reads inside the city
      const padx = (maxx - minx) * 1.2, pady = (maxy - miny) * 1.2;
      map.fitBounds([[minx - padx, miny - pady], [maxx + padx, maxy + pady]], { duration: 1400 });
    } else {
      src?.setData({ type: "FeatureCollection", features: [] });
      map.flyTo({ center: city.coordinates, zoom: 6.8, duration: 1000 });
    }
  }, [ready, selected, cities, compact]);

  const selectedCity = cities.find((c) => c.id === selected);

  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" data-testid="india-map" />
      {selected && (
        <button onClick={() => cbs.current.onSelect?.(null)}
          className="absolute top-3 left-3 z-10 inline-flex items-center gap-1.5 rounded-lg border border-line-2 bg-panel/95 px-3 py-1.5 text-[12.5px] shadow-sm hover:border-accent/50">
          <Icon name="fit" className="h-3.5 w-3.5" /> Back to India
        </button>
      )}
      {selectedCity?.status === "demo" && selectedCity.test_area && (
        <div className={clsx("absolute inset-x-0 bottom-4 z-10 flex justify-center", compact && "bottom-2")}>
          <button onClick={() => cbs.current.onExplore?.()}
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-[13.5px] font-medium text-white shadow-lg shadow-accent/25 hover:bg-[#0d9488]">
            Explore harmonized parcels <Icon name="arrow" className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
