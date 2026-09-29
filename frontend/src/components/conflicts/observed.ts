import { fmtArea, fmtValue } from "@/lib/format";
import type { ConflictOut } from "@/lib/types";

export function observedText(c: ConflictOut): string {
  const { a, b, delta } = c.observed ?? {};
  if (c.conflict_type === "AREA_MISMATCH") return `${fmtArea(a as number)} vs ${fmtArea(b as number)} (${delta})`;
  if (c.conflict_type === "TOPOLOGY") return `${String(a).replaceAll("_", " ").toLowerCase()}${b ? ` with ${b}` : ""} · ${delta}`;
  if (c.conflict_type === "MISSING_ATTRIBUTE") return `${c.field?.replace("_", " ")} missing in ${c.source_b}`;
  return `${fmtValue(a)} vs ${fmtValue(b)}${delta ? ` (${delta})` : ""}`;
}
