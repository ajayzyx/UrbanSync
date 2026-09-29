import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "vitest";

/** Dark-theme-only colors that are unreadable on the light surfaces. */
const FORBIDDEN = ["#fca5a5", "#fecaca", "#e8eaed", "#0a0c0f", "#11151a", "#2dd4bf"];

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (/\.(tsx?|css)$/.test(name) && !name.endsWith(".test.ts")) out.push(p);
  }
  return out;
}

describe("light theme", () => {
  test("no dark-theme-only colors remain in components or styles", () => {
    const offenders: string[] = [];
    for (const f of walk(join(__dirname, ".."))) {
      const s = readFileSync(f, "utf8").toLowerCase();
      for (const hex of FORBIDDEN) if (s.includes(hex)) offenders.push(`${f.split("/src/")[1]}: ${hex}`);
    }
    expect(offenders).toEqual([]);
  });
});
