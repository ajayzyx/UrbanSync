import { describe, expect, test } from "vitest";
import { STATIC_CITIES } from "./cities";

describe("static city registry (offline fallback)", () => {
  test("mirrors the backend registry shape", () => {
    expect(STATIC_CITIES).toHaveLength(8);
    expect(STATIC_CITIES.filter((c) => c.status === "demo").map((c) => c.id)).toEqual(["pune"]);
    expect(STATIC_CITIES.filter((c) => c.status === "validation").map((c) => c.id)).toEqual(["surat"]);
  });
  test("carries no statistics — numbers only ever come from the backend", () => {
    for (const c of STATIC_CITIES) {
      expect(c.stats).toBeNull();
      expect(c.validation).toBeNull();
      expect(c.test_area).toBeNull();
    }
  });
});
