"use client";

import { useEffect, useState } from "react";

type Hero = { w: number; h: number; states: string; cities: { id: string; name: string; status: string; x: number; y: number }[] };

/** Landing hero: real India geography as a light SVG with city nodes and subtle connections.
 *  Falls back to a plain panel if the vendored file cannot load. */
export function IndiaHero() {
  const [hero, setHero] = useState<Hero | null | undefined>(undefined);
  useEffect(() => {
    fetch("/geo/india-hero.json").then((r) => (r.ok ? r.json() : Promise.reject())).then(setHero).catch(() => setHero(null));
  }, []);

  if (hero === null) return <div aria-hidden="true" className="absolute inset-0 bg-[radial-gradient(ellipse_at_70%_35%,rgba(15,118,110,0.08),transparent_60%)]" />;
  if (!hero) return null;
  const demo = hero.cities.find((c) => c.status === "demo");

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute top-1/2 -right-[26%] w-[88%] -translate-y-1/2 opacity-[0.96] sm:-right-[10%] sm:w-[62%] lg:right-[2%] lg:w-[46%]">
        <svg viewBox={`0 0 ${hero.w} ${hero.h}`} className="hero-field h-auto w-full">
          <path d={hero.states} fill="#eef0eb" stroke="#c9cdc2" strokeWidth={1.1} />
          {demo &&
            hero.cities.filter((c) => c.id !== demo.id).map((c) => (
              <line key={c.id} x1={demo.x} y1={demo.y} x2={c.x} y2={c.y} stroke="#0f766e" strokeWidth={0.8}
                strokeDasharray="3 6" opacity={0.35} className="hero-link" />
            ))}
          {hero.cities.map((c) => (
            <g key={c.id}>
              <circle cx={c.x} cy={c.y} r={c.status === "demo" ? 7 : 4.5}
                fill={c.status === "planned" ? "#aab3ad" : c.status === "validation" ? "#ffffff" : "#0f766e"}
                stroke={c.status === "planned" ? "#ffffff" : "#0f766e"} strokeWidth={c.status === "validation" ? 2.5 : 2} />
              {c.status === "demo" && <circle cx={c.x} cy={c.y} r={7} fill="none" stroke="#0f766e" strokeWidth={2} className="hero-ping" />}
              <text x={c.x + 11} y={c.y + 4} fontSize={15} fontWeight={c.status === "demo" ? 650 : 480}
                fill={c.status === "demo" ? "#0f766e" : "#6b7480"}>{c.name}</text>
            </g>
          ))}
          {demo && (
            <g>
              <rect x={demo.x + 8} y={demo.y + 12} rx={5} width={112} height={24} fill="#ffffff" stroke="#0f766e55" />
              <text x={demo.x + 18} y={demo.y + 28} fontSize={12.5} fontWeight={600} fill="#0f766e">Demo dataset</text>
            </g>
          )}
        </svg>
      </div>
      <div className="absolute inset-0 bg-[linear-gradient(90deg,var(--bg)_0%,rgba(247,246,243,0.9)_38%,rgba(247,246,243,0.25)_60%,transparent_100%)]" />
      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-bg" />
    </div>
  );
}
