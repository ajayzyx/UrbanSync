const PATHS: Record<string, string> = {
  dashboard: "M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z",
  layers: "M12 3 2 8l10 5 10-5-10-5zM2 13l10 5 10-5M2 17.5l10 5 10-5",
  flow: "M4 6h6M4 12h10M4 18h16M14 6l3 0M18 12h2",
  map: "M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14",
  alert: "M12 3 2 20h20L12 3zM12 10v4M12 17h.01",
  chart: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM21 21l-5-5",
  upload: "M12 16V4M6 10l6-6 6 6M4 20h16",
  check: "M5 12l5 5L20 7",
  x: "M6 6l12 12M18 6 6 18",
  fit: "M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5",
  play: "M7 4v16l13-8z",
  refresh: "M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7",
  arrow: "M5 12h14M13 6l6 6-6 6",
  globe: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM2 12h20M12 2c3 3.5 3 16.5 0 20M12 2c-3 3.5-3 16.5 0 20",
  info: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 11v6M12 7h.01",
};

export function Icon({ name, className = "h-4 w-4" }: { name: keyof typeof PATHS | string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round"
      strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={PATHS[name] ?? PATHS.info} />
    </svg>
  );
}
