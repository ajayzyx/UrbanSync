"use client";

import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { classLabel, conflictTypeLabel, STATUS_COLORS } from "@/lib/format";
import type { Analytics } from "@/lib/types";

const AXIS = { fill: "#5b6572", fontSize: 11 };
const GRID = "rgba(23,32,42,0.07)";
const ACCENT = "#0f766e";
const NEUTRAL = "#8fa0ae";

function Tip({ active, payload, label, unit = "" }: { active?: boolean; payload?: { value: number; payload: Record<string, unknown> }[]; label?: string; unit?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-line-2 bg-panel px-2.5 py-1.5 text-[12px] shadow-lg">
      <div className="text-muted">{String(payload[0].payload.name ?? label)}</div>
      <div className="tabular font-medium text-text">{payload[0].value.toLocaleString("en-IN")}{unit}</div>
    </div>
  );
}

/** Match status distribution — status colours always paired with a text label. */
export function MatchDistribution({ data }: { data: Analytics["match_distribution"] }) {
  const rows = data.map((d) => ({ name: classLabel(d.class), value: d.count, color: STATUS_COLORS[d.class] }));
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 44, top: 4, bottom: 4 }} barCategoryGap={6}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={124} tick={AXIS} axisLine={false} tickLine={false} />
        <Tooltip content={<Tip unit=" parcels" />} cursor={{ fill: "rgba(23,32,42,0.04)" }} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {rows.map((r) => <Cell key={r.name} fill={r.color} />)}
          <LabelList dataKey="value" position="right" fill="#1b2430" fontSize={11} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ConfidenceHistogram({ data }: { data: Analytics["confidence_histogram"] }) {
  const rows = data.filter((d) => d.bin !== "n/a").map((d) => ({ name: d.bin, value: d.count }));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={rows} margin={{ left: -12, right: 8, top: 8, bottom: 0 }} barCategoryGap={2}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="name" tick={{ ...AXIS, fontSize: 10 }} tickFormatter={(v: string) => v.split("–")[0]} axisLine={false} tickLine={false} />
        <YAxis tick={AXIS} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip content={<Tip unit=" parcels" />} cursor={{ fill: "rgba(23,32,42,0.04)" }} />
        <Bar dataKey="value" fill={ACCENT} radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function HBars({ data, height }: { data: { name: string; value: number }[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height ?? Math.max(120, data.length * 30 + 10)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 44, top: 4, bottom: 4 }} barCategoryGap={6}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={136} tick={AXIS} axisLine={false} tickLine={false} />
        <Tooltip content={<Tip />} cursor={{ fill: "rgba(23,32,42,0.04)" }} />
        <Bar dataKey="value" fill={NEUTRAL} radius={[0, 4, 4, 0]} isAnimationActive={false}>
          <LabelList dataKey="value" position="right" fill="#1b2430" fontSize={11} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function conflictRows(data: Analytics["conflict_breakdown"]) {
  return data.map((d) => ({ name: conflictTypeLabel(d.type), value: d.count }));
}
