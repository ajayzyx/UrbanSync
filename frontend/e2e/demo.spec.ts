import { expect, test, type Page } from "@playwright/test";

async function mapReady(page: Page) {
  await page.waitForFunction(() => {
    const m = (window as unknown as { __urbansyncMap?: { getSource: (id: string) => unknown; loaded: () => boolean } }).__urbansyncMap;
    return !!m && !!m.getSource("parcels") && m.loaded();
  }, null, { timeout: 30_000 });
}

test("full SIH demo loop", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /Explore India Map/ }).click();
  await expect(page).toHaveURL(/\/app\/india/);

  await page.goto("/app/sources");
  await expect(page.getByText("EPSG:32643").first()).toBeVisible();

  await page.getByRole("link", { name: "Harmonize" }).first().click();
  await page.getByRole("button", { name: /harmonization/i }).click();
  await expect(page.getByTestId("stage-harmonize")).toHaveAttribute("data-status", "done", { timeout: 60_000 });
  await expect(page.getByText("Schema mapping to canonical fields")).toBeVisible();

  await page.goto("/app/map?parcel=P1023");
  await expect(page.getByText("Why was this matched?")).toBeVisible();
  await expect(page.getByText("Reason:").first()).toBeVisible();
  await expect(page.getByText("not a legal determination")).toBeVisible();

  await page.goto("/app/conflicts?type=area");
  await page.getByRole("row").nth(1).click();
  await expect(page.getByText("Why was this flagged?")).toBeVisible();
  await expect(page.getByText("Source values side-by-side")).toBeVisible();
  await page.getByRole("button", { name: "Use cadastral" }).click();
  await expect(page.getByText("source records unchanged")).toBeVisible();

  await page.getByRole("link", { name: "Analytics" }).first().click();
  await expect(page.getByText("Before vs after")).toBeVisible();
  await expect(page.getByText("Evaluated on synthetic ground truth")).toBeVisible();
});

test("clicking a parcel on the map opens its drawer", async ({ page }) => {
  await page.goto("/app/map");
  await mapReady(page);
  const pt = await page.evaluate(() => {
    const m = (window as unknown as { __urbansyncMap: { queryRenderedFeatures: (o: object) => { properties: { parcel_id: string }; geometry: { coordinates: number[][][] } }[]; project: (c: number[]) => { x: number; y: number }; getCanvas: () => HTMLCanvasElement } }).__urbansyncMap;
    const f = m.queryRenderedFeatures({ layers: ["parcels-fill"] })[40];
    const ring = f.geometry.coordinates[0];
    const c = [ring.reduce((s, p) => s + p[0], 0) / ring.length, ring.reduce((s, p) => s + p[1], 0) / ring.length];
    const p = m.project(c);
    const r = m.getCanvas().getBoundingClientRect();
    return { x: r.left + p.x, y: r.top + p.y, id: f.properties.parcel_id };
  });
  await page.mouse.click(pt.x, pt.y);
  await expect(page).toHaveURL(new RegExp(`parcel=${pt.id}`));
  await expect(page.getByLabel(`Parcel ${pt.id} details`)).toBeVisible();
});

test("backend offline shows banner, not blank", async ({ page }) => { // Review Focus 5
  await page.route("http://localhost:8000/**", (r) => r.abort());
  await page.goto("/app/map");
  await expect(page.getByText("Backend offline")).toBeVisible();
  await expect(page.getByText(/Backend unreachable/).first()).toBeVisible();
});

test("mobile layout has no horizontal scroll", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  for (const p of ["/", "/app", "/app/india", "/app/sources", "/app/harmonize", "/app/map", "/app/conflicts", "/app/analytics"]) {
    await page.goto(p);
    await page.waitForTimeout(800);
    const width = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(width, p).toBeLessThanOrEqual(375);
  }
});

test("India map drill-down to parcels", async ({ page }) => {
  await page.goto("/app/india");
  await expect(page.getByText("8 city profiles")).toBeVisible();
  await page.getByRole("button", { name: "Pune", exact: true }).click(); // DOM marker
  await expect(page.getByText("Demo / Synthetic Dataset").first()).toBeVisible();
  await page.getByRole("button", { name: "Explore harmonized parcels" }).click({ timeout: 15_000 });
  await expect(page).toHaveURL(/\/app\/map/);
});

test("planned city is honest", async ({ page }) => { // Review Focus 2
  await page.goto("/app/india?city=mumbai");
  await expect(page.getByText("Dataset not connected yet.")).toBeVisible();
  await expect(page.getByText("Demo / Synthetic Dataset")).toHaveCount(0);
  await page.getByRole("textbox", { name: /Search a city/i }).fill("Delhi");
  await expect(page.getByText("○ Planned").first()).toBeVisible();
  await page.getByRole("textbox", { name: /Search a city/i }).fill("Varanasi");
  await expect(page.getByText("No city found")).toBeVisible();
});

test("no BhoomiSync anywhere; UrbanSync titles", async ({ page }) => { // Review Focus 5
  for (const p of ["/", "/app", "/app/india"]) {
    await page.goto(p);
    await page.waitForTimeout(600);
    await expect(page).toHaveTitle(/UrbanSync AI/);
    expect(await page.locator("body").innerText(), p).not.toContain("BhoomiSync");
  }
});

test("India map with geo asset blocked shows error, not blank", async ({ page }) => { // Review Focus 4
  await page.route("**/geo/india-states.json", (r) => r.abort());
  await page.goto("/app/india");
  await expect(page.getByText("Could not load data")).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry" })).toBeVisible();
});
