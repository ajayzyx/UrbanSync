"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { API_URL, apiGet, useInterval } from "@/lib/api";
import { demoCity } from "@/lib/cities";
import { fmtTime } from "@/lib/format";
import type { Run } from "@/lib/types";
import { Icon } from "./Icon";
import { ToastProvider } from "./Toast";

const NAV = [
  { href: "/app", label: "Command Center", mobileLabel: "Home", icon: "dashboard" },
  { href: "/app/sources", label: "Data Sources", mobileLabel: "Data", icon: "layers" },
  { href: "/app/harmonize", label: "Harmonize", mobileLabel: "Run", icon: "flow" },
  { href: "/app/map", label: "Land Intelligence", mobileLabel: "Map", icon: "map" },
  { href: "/app/conflicts", label: "Conflicts", mobileLabel: "Conflicts", icon: "alert" },
  { href: "/app/analytics", label: "Analytics", mobileLabel: "Analytics", icon: "chart" },
];

type Health = { ok: boolean; db: boolean } | null;

function useHealth() {
  const [health, setHealth] = useState<Health>(null);
  const [run, setRun] = useState<Run | null>(null);
  const check = () => {
    apiGet<{ database: string }>("/health")
      .then((h) => setHealth({ ok: true, db: h.database === "ok" }))
      .catch(() => setHealth({ ok: false, db: false }));
    apiGet<Run>("/harmonization/latest").then(setRun).catch(() => setRun(null));
  };
  useEffect(check, []);
  useInterval(check, 8000);
  return { health, run, check };
}

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className="flex items-center gap-2.5">
      <svg viewBox="0 0 32 32" className="h-7 w-7 shrink-0" aria-hidden="true">
        <rect x="1" y="1" width="30" height="30" rx="8" fill="var(--panel-2)" stroke="var(--line-2)" />
        <path d="M8 10h7v6H8zM17 10h7v12h-7zM8 18h7v4H8z" fill="none" stroke="var(--accent)" strokeWidth="1.4" />
      </svg>
      {!compact && (
        <span className="font-display text-[15px] font-semibold tracking-tight">
          UrbanSync <span className="text-accent">AI</span>
        </span>
      )}
    </Link>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const { health, run, check } = useHealth();
  const offline = health !== null && !health.ok;
  const dbDown = health !== null && health.ok && !health.db;
  const active = (href: string) => (href === "/app" ? path === "/app" : path.startsWith(href));
  const apiTone = health === null ? "bg-idle" : health.ok ? "bg-ok" : "bg-bad";
  const databaseTone = health === null ? "bg-idle" : health.db ? "bg-ok" : "bg-bad";
  const engineReady = health?.ok === true && health.db;

  return (
    <ToastProvider>
      <div className="grid-bg flex min-h-screen">
        <aside className="fixed inset-y-0 left-0 z-40 hidden w-[68px] flex-col border-r border-line bg-panel md:flex lg:w-[220px]">
          <div className="flex h-14 items-center border-b border-line px-4 lg:px-5">
            <span className="lg:hidden"><Logo compact /></span>
            <span className="hidden lg:block"><Logo /></span>
          </div>
          <div className="hidden px-5 pt-5 pb-2 micro lg:block">Workspace</div>
          <nav aria-label="Workspace" className="mt-2 flex flex-col gap-1 px-2.5 lg:mt-0">
            {NAV.map((n) => (
              <Link key={n.href} href={n.href} title={n.label} aria-current={active(n.href) ? "page" : undefined}
                className={clsx(
                  "flex items-center gap-3 rounded-lg border px-3 py-2.5 text-[13px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                  active(n.href) ? "border-accent/20 bg-accent/10 text-accent" : "border-transparent text-muted hover:bg-bg-2 hover:text-text",
                )}>
                <Icon name={n.icon} className="h-[18px] w-[18px] shrink-0" />
                <span className="hidden lg:inline">{n.label}</span>
              </Link>
            ))}
          </nav>
          <div className="mt-auto hidden border-t border-line p-4 lg:block">
            <div className="micro mb-3">System status</div>
            <div className="space-y-2.5 text-[11.5px]">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted">API</span>
                <span className="inline-flex items-center gap-1.5 text-text">
                  <span className={clsx("h-1.5 w-1.5 rounded-full", apiTone)} />
                  {health === null ? "Checking" : health.ok ? "Online" : "Offline"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted">Database</span>
                <span className="inline-flex items-center gap-1.5 text-text">
                  <span className={clsx("h-1.5 w-1.5 rounded-full", databaseTone)} />
                  {health === null ? "Checking" : health.db ? "Connected" : "Unavailable"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted">Harmonization</span>
                <span className="inline-flex items-center gap-1.5 text-text">
                  <span className={clsx("h-1.5 w-1.5 rounded-full", engineReady ? "bg-ok" : "bg-idle")} />
                  {engineReady ? "Ready" : "Unavailable"}
                </span>
              </div>
            </div>
            <div className="mt-4 mb-2 inline-flex items-center gap-1.5 rounded-md border border-line-2 bg-panel-2 px-2 py-1 text-[11px] font-medium text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" /> Demo Workspace
            </div>
            <p className="text-[11px] leading-relaxed text-faint">
              Decision-support prototype on synthetic data for SIH26013. Not a legal record.
            </p>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col md:pl-[68px] lg:pl-[220px]">
          <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-2 border-b border-line bg-panel px-3 md:gap-4 md:px-6">
            <div className="flex min-w-0 items-center gap-2 md:gap-4">
              <div className="md:hidden"><Logo /></div>
              <Link href="/app/india" aria-label={`${demoCity().name} demo ward, open city map`}
                className="inline-flex min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-[12px] text-muted transition-colors hover:bg-bg-2 hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
                <Icon name="globe" className="h-4 w-4 shrink-0 text-accent" />
                <span className="truncate">{demoCity().name}<span className="hidden sm:inline"> · Demo ward</span></span>
              </Link>
              <Link href="/app/map" aria-label="Search parcels" title="Search parcels"
                className="inline-flex items-center gap-2 rounded-md border border-line-2 px-2.5 py-1.5 text-[12px] text-muted transition-colors hover:border-accent/40 hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
                <Icon name="search" className="h-3.5 w-3.5" />
                <span className="hidden xl:inline">Search</span>
              </Link>
            </div>
            <div className="flex shrink-0 items-center gap-2 text-[11.5px] text-muted sm:gap-3 md:gap-4">
              <span className="hidden items-center gap-1.5 xl:inline-flex" aria-live="polite">
                <span className={clsx("h-1.5 w-1.5 rounded-full", run?.status === "running" ? "pulse-dot bg-accent" :
                  run?.status === "completed" ? "bg-ok" : run?.status === "failed" ? "bg-bad" : "bg-idle")} />
                {run ? `Run #${run.id} · ${run.status === "running" ? "running" : run.status === "failed" ? "failed" : fmtTime(run.finished_at)}` : "No harmonization run"}
              </span>
              <span className="inline-flex items-center gap-1.5" title={`API: ${API_URL}`}>
                <span className={clsx("h-1.5 w-1.5 rounded-full", apiTone)} />
                <span className="hidden sm:inline">API</span>
              </span>
              <span className="inline-flex items-center gap-1.5" title="PostGIS database">
                <span className={clsx("h-1.5 w-1.5 rounded-full", databaseTone)} />
                <span className="hidden md:inline">PostGIS</span>
              </span>
            </div>
          </header>

          {(offline || dbDown) && (
            <div role="alert" className="flex flex-wrap items-center justify-between gap-3 border-b border-bad/30 bg-bad/[0.08] px-4 py-2.5 text-[13px] text-bad md:px-6">
              <span>
                {offline ? (
                  <>Backend offline — start it with <code className="rounded bg-black/[0.05] px-1.5 py-0.5 font-mono text-[12px]">uv run uvicorn app.main:app</code></>
                ) : (
                  <>Database unavailable — start it with <code className="rounded bg-black/[0.05] px-1.5 py-0.5 font-mono text-[12px]">docker compose up -d</code></>
                )}
              </span>
              <button onClick={check} className="rounded-md border border-bad/40 px-2.5 py-1 text-[12px] hover:bg-bad/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-bad">Retry</button>
            </div>
          )}

          <main className="flex-1 pb-20 md:pb-0">{children}</main>
        </div>

        <nav aria-label="Workspace" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-6 border-t border-line bg-panel pb-[env(safe-area-inset-bottom)] md:hidden">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} aria-label={n.label} aria-current={active(n.href) ? "page" : undefined}
              className={clsx("flex min-w-0 flex-col items-center gap-1 py-2.5 text-[9.5px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent", active(n.href) ? "text-accent" : "text-muted")}>
              <Icon name={n.icon} className="h-[18px] w-[18px]" />
              <span className="max-w-full truncate px-0.5">{n.mobileLabel}</span>
            </Link>
          ))}
        </nav>
      </div>
    </ToastProvider>
  );
}

export function PageHeader({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 px-4 pt-6 pb-4 md:px-6">
      <div>
        <div className="micro mb-1 text-accent/80">{eyebrow}</div>
        <h1 className="font-display text-[22px] font-medium tracking-tight md:text-[26px]">{title}</h1>
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </div>
  );
}
