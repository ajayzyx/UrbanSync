"use client";

import Link from "next/link";
import { IndiaHero } from "../india/IndiaHero";
import { Logo } from "../ui/Shell";

export function Hero() {
  const delay = (d: number) => ({ animationDelay: `${d}s` });
  return (
    <section className="relative min-h-[80svh] overflow-hidden">
      <IndiaHero />
      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-4 py-5 md:px-6">
        <Logo />
        <Link href="/app" className="rounded-lg border border-line-2 bg-panel/70 px-3 py-1.5 text-[13px] text-muted backdrop-blur hover:text-text">
          Workspace
        </Link>
      </header>
      <div className="relative z-10 mx-auto flex max-w-6xl flex-col px-4 pt-[9vh] pb-24 md:px-6">
        <div style={delay(0)} className="rise micro text-accent">India&apos;s urban spatial intelligence layer</div>
        <h1 style={delay(0.08)}
          className="rise font-display mt-4 max-w-2xl text-[42px] leading-[1.04] font-medium tracking-tight text-balance md:text-[66px]">
          One spatial view.<br />Many urban data sources.
        </h1>
        <p style={delay(0.16)} className="rise mt-5 max-w-xl text-[16.5px] leading-relaxed text-muted">
          UrbanSync AI harmonizes fragmented cadastral, municipal, revenue, survey and geospatial datasets into a
          unified, explainable urban land view.
        </p>
        <div style={delay(0.24)} className="rise mt-8 flex flex-wrap items-center gap-3">
          <Link href="/app/india"
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-3 text-[15px] font-medium text-white shadow-lg shadow-accent/20 hover:bg-[#0d9488]">
            Explore India Map <span aria-hidden="true">→</span>
          </Link>
          <Link href="/#how" className="rounded-lg border border-line-2 bg-panel/70 px-5 py-3 text-[15px] backdrop-blur hover:border-accent/50">
            See How It Works
          </Link>
        </div>
        <div style={delay(0.32)} className="rise mt-10 flex flex-wrap items-center gap-x-5 gap-y-1 text-[12px] text-faint">
          <span>Intelligent spatial data harmonization for India&apos;s cities.</span>
          <span className="hidden h-3 w-px bg-line-2 sm:block" />
          <span>Demonstrated with controlled test data · SIH26013</span>
        </div>
      </div>
    </section>
  );
}
