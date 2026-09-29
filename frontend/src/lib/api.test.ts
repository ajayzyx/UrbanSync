import { afterEach, describe, expect, test, vi } from "vitest";
import { apiGet, apiPost } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  test("surfaces unreachable backend", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));
    await expect(apiGet("/datasets")).rejects.toMatchObject({
      status: 0,
      message: expect.stringContaining("Backend unreachable"),
    });
  });
  test("surfaces 422 detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Unsupported file type" }), { status: 422 })),
    );
    await expect(apiGet("/x")).rejects.toMatchObject({ status: 422, message: "Unsupported file type" });
  });
  test("posts JSON and parses response", async () => {
    const f = vi.fn().mockResolvedValue(new Response(JSON.stringify({ run_id: 3 }), { status: 202 }));
    vi.stubGlobal("fetch", f);
    await expect(apiPost("/harmonize")).resolves.toEqual({ run_id: 3 });
    expect(f.mock.calls[0][1].method).toBe("POST");
  });
});
