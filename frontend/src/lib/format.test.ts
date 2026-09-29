import { describe, expect, test } from "vitest";
import { classLabel, conflictTypeLabel, fmtArea, pct, statusColor } from "./format";

describe("format", () => {
  test("statusColor", () => {
    expect(statusColor("HARMONIZED")).toBe("#15803d");
    expect(statusColor("REVIEW")).toBe("#b45309");
    expect(statusColor("CONFLICT")).toBe("#b91c1c");
    expect(statusColor("UNMATCHED")).toBe("#64748b");
  });
  test("pct handles null", () => {
    expect(pct(0.934)).toBe("93%");
    expect(pct(null)).toBe("—");
    expect(pct(0.9424, 1)).toBe("94.2%");
  });
  test("labels", () => {
    expect(conflictTypeLabel("AREA_MISMATCH")).toBe("Area mismatch");
    expect(conflictTypeLabel("MISSING_ATTRIBUTE")).toBe("Missing attribute");
    expect(classLabel("HIGH")).toBe("High confidence");
    expect(classLabel("HARMONIZED")).toBe("High confidence");
  });
  test("fmtArea", () => {
    expect(fmtArea(420.04)).toBe("420 m²");
    expect(fmtArea(null)).toBe("—");
  });
});

describe("parcelStatusLabel", () => {
  test("HARMONIZED with any non-HIGH primary match was confirmed by a reviewer", async () => {
    const { parcelStatusLabel } = await import("./format");
    expect(parcelStatusLabel("HARMONIZED", ["REVIEW", "HIGH"])).toBe("Reviewer-confirmed");
    expect(parcelStatusLabel("HARMONIZED", ["HIGH", "HIGH"])).toBe("High confidence");
    expect(parcelStatusLabel("REVIEW", ["REVIEW"])).toBe("Review");
  });
});

describe("resolvableSources", () => {
  test("only sources with a value for the field are offered", async () => {
    const { resolvableSources } = await import("./format");
    const sv = { cadastral: { owner_name: "A B" }, municipal: { owner_name: null }, revenue: { owner_name: "A B" } };
    expect(resolvableSources(sv, "owner_name")).toEqual(["cadastral", "revenue"]);
  });
});
