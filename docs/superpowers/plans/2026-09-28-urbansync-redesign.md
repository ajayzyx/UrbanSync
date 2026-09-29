# UrbanSync AI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve the working BhoomiSync MVP into **UrbanSync AI**: an India-first, premium light-themed urban geospatial intelligence platform, with an interactive India map → city → tested-area → parcel drill-down, a multi-city architecture, an honest problem/use-case story on the landing page, and a second synthetic city proving the engine is city-agnostic — without breaking the existing harmonization engine, APIs, or demo flow.

**Architecture:** The backend gains one thin layer: a `CityProfile` registry (`app/cities.py`), a city-parametrized synthetic generator, `GET /cities` (live stats for the demo city, honest nulls elsewhere), and a validation CLI that runs the *unchanged* engine on a second city. The frontend swaps the design tokens to a light theme, adds an `/app/india` MapLibre page (vendored DataMeet state boundaries, DOM city markers — no external tiles or glyph servers), rebuilds the landing page around the India story, and keeps every existing workspace page, API call and e2e-tested workflow intact.

**Tech Stack:** unchanged (FastAPI + GeoPandas + PostGIS; Next 16 + MapLibre + Tailwind v4 + Recharts; Playwright/vitest/pytest) + vendored `india-states.json` (DataMeet, CC-BY 4.0) + Higgsfield CLI for one hero asset.

**Spec:** [docs/prd-v2.md](../../prd-v2.md) (v1 spec: [docs/prd.md](../../prd.md) still governs the harmonization engine)

## Global Constraints

- **Demo city: Pune** — the existing ward *is* at Pune's coordinates and spec §6 says "If an existing test dataset already corresponds to a city, use that city." Configurable via `settings.demo_city`; switching cities later = config change + reseed.
- **Validation city: Surat**, `seed=11`, origin `(72.8311, 21.1702)`. Always labelled "Synthetic validation dataset".
- City registry (id, name, state, lon, lat, status): ahmedabad/Gujarat/72.5714,23.0225 · delhi/Delhi/77.2090,28.6139 · mumbai/Maharashtra/72.8777,19.0760 · bengaluru/Karnataka/77.5946,12.9716 · hyderabad/Telangana/78.4867,17.3850 · **pune**/Maharashtra/73.8567,18.5204/`demo` · jaipur/Rajasthan/75.7873,26.9124 · **surat**/Gujarat/72.8311,21.1702/`validation`; all others `planned`.
- Light design tokens (CSS vars, exact): `--bg #f7f6f3`, `--bg-2 #f1efea`, `--panel #ffffff`, `--panel-2 #faf9f6`, `--line rgba(23,32,42,0.08)`, `--line-2 rgba(23,32,42,0.14)`, `--text #1b2430`, `--muted #5b6572`, `--faint #8b94a0`, `--accent #0f766e`, `--accent-dim rgba(15,118,110,0.08)`.
- Status colors (light surfaces): HARMONIZED `#15803d`, REVIEW `#b45309`, CONFLICT `#b91c1c`, UNMATCHED `#64748b`. Conflict-status pills: Pending `#b45309`, Accepted `#0f766e`, Resolved `#15803d`, Ignored `#64748b`.
- Map style (light): map background `#f2f1ec`; India states fill `#f8f7f3`, stroke `#cfccc0`; roads `#e3e1d8`; buildings `#b6bcc4` @0.35; parcel fills status colors @0.25 with full-color 0.8px lines; test-area highlight fill `#0f766e` @0.10 + 1.5px line; selected parcel `#0f766e` 2.8px.
- Copy, exact: name **UrbanSync AI**; tagline "Intelligent spatial data harmonization for India's cities."; hero eyebrow "INDIA'S URBAN SPATIAL INTELLIGENCE LAYER"; H1 "One spatial view.\nMany urban data sources."; hero sub "UrbanSync AI harmonizes fragmented cadastral, municipal, revenue, survey and geospatial datasets into a unified, explainable urban land view."; CTAs "Explore India Map" → `/app/india`, "See How It Works" → `/#how`; planned-city line "Dataset not connected yet."; demo badge "Demo / Synthetic Dataset"; sidebar footer "Demo Workspace".
- **No fake metrics**: every number shown for the demo city comes from `/cities` (live DB); planned cities show no numbers; validation numbers come from a real engine run persisted by the validation CLI.
- No external runtime dependencies: India boundaries vendored in-repo; no tile/glyph servers (city labels are DOM markers, not MapLibre symbol layers).
- Do not break: all existing backend tests (104+), the parcel-GIS e2e flow strings ("Why was this matched?", "Why was this flagged?", "source records unchanged", "Backend offline", stage testids), and `/app/map` behavior.
- No visible "BhoomiSync" anywhere in `frontend/src`, backend API responses, or README product naming (a historical "formerly/SIH26013" note in docs is allowed only in `docs/prd.md`).
- India boundary attribution: footer line "India boundaries: DataMeet community maps (CC-BY 4.0)" on landing + README.

## Review Focus

1. **Backend down or seeded-but-never-run DB while viewing `/app/india` or the landing page** — expected: honest placeholders ("Run harmonization to see match stats") or error states, never fabricated 984/43/91.4-style numbers and never a blank page. Pinned in Task 2 (`/cities` nulls) and Task 8 (e2e with routes aborted).
2. **Interacting with a planned city (click, search, deep-link `/app/india?city=mumbai`)** — expected: "Dataset not connected yet." messaging, no demo-city stats leaking onto it, no 500s. Pinned in Task 4 (unit-ish) and Task 8 (e2e).
3. **Theme overhaul regressing the tested parcel workflow** — the old e2e suite (map click-select, conflict resolve, offline banner, mobile no-h-scroll) must pass unchanged on the light theme, and text must stay readable (Lighthouse accessibility ≥ 90). Pinned in Task 8.
4. **Missing/corrupt vendored geography** (`/geo/india-states.json` fails to load) — expected: `/app/india` shows an ErrorState with Retry and the landing hero falls back to a plain styled panel; never a blank hero or crashed page. Pinned in Task 4 (error path) and Task 5 (hero fallback).
5. **Rename leakage** — a stray "BhoomiSync" in a title, toast, README heading or API string. Pinned in Task 1 (grep gate + title test) and Task 8 (e2e title assertions).

---

## File Structure

```
backend/app/cities.py              # CITY_PROFILES registry + city lookup (NEW)
backend/app/synthetic.py           # generate_ward(out_dir, seed, origin_lonlat=PUNE) (MOD)
backend/app/validate.py            # python -m app.validate → data/validation/<city>.json via real engine (NEW)
backend/app/api/cities.py          # GET /cities, GET /cities/{id} (NEW)
backend/app/config.py              # demo_city="pune", validation_dir (MOD)
backend/tests/test_cities.py       # registry, endpoint, validation, city-agnostic engine (NEW)
frontend/public/geo/india-states.json   # vendored, simplified DataMeet ADM1 (NEW, committed)
frontend/public/geo/india-hero.json     # build-time SVG-path snapshot for the landing hero (NEW, committed)
frontend/scripts/fetch-india-geo.mjs    # one-time fetch + simplify + hero snapshot (NEW)
frontend/src/lib/cities.ts         # CityProfile type + static fallback registry (NEW)
frontend/src/components/india/IndiaMap.tsx      # interactive MapLibre India map (NEW)
frontend/src/components/india/CityCard.tsx      # hover/selected city card (NEW)
frontend/src/components/india/IndiaHero.tsx     # SVG hero for landing (NEW)
frontend/src/app/app/india/page.tsx             # India Map page (NEW)
frontend/src/app/page.tsx + components/landing/*  # rebuilt (MOD)
frontend/src/app/globals.css, lib/format.ts, components/map/layers.ts, ui/*  # light theme (MOD)
docs/demo-script.md, README.md     # updated journey (MOD)
```

---

### Task 1: Rebrand to UrbanSync AI + light design system

**Files:**
- Modify: `frontend/src/lib/format.ts`, `frontend/src/lib/format.test.ts`, `frontend/src/app/globals.css`, `frontend/src/app/layout.tsx` (metadata), `frontend/src/components/ui/{Shell,Panel,StatusPill,States,Kpi,Toast,Icon}.tsx`, `frontend/src/components/map/layers.ts`, `frontend/src/components/dashboard/Charts.tsx`, `frontend/src/components/parcel/ConfidenceBars.tsx`, `backend/app/main.py` (FastAPI title → "UrbanSync AI"), `README.md`, `docs/demo-script.md` (name only; journey updated in Task 8)

**Interfaces:**
- Produces: the Global Constraints token set as CSS vars; `STATUS_COLORS` with the light-theme hexes; `Logo` renders "UrbanSync AI" (keep the parcel-grid mark, teal on white); metadata title "UrbanSync AI — Intelligent spatial data harmonization for India's cities". Everything else keeps its existing exports/signatures.

- [ ] **Step 1: Update the failing unit tests** — in `format.test.ts` pin the new hexes (`#15803d`, `#b45309`, `#b91c1c`, `#64748b`); run `npm test`, expect FAIL on the four color assertions.
- [ ] **Step 2: Implement** — swap `:root` tokens in `globals.css` (grid-bg lines become `rgba(23,32,42,0.04)`; hero-scan/teal keyframes re-tinted for light; maplibre popup/ctrl overrides for light); update `STATUS_COLORS` + `CONFLICT_STATUS` pills; re-tint chart constants (`AXIS` fill `#5b6572`, grid `rgba(23,32,42,0.07)`, neutral `#8fa0ae`, accent `#0f766e`); map layer palette per Global Constraints; buttons (`primary` = accent bg, white text), pills, skeletons (`bg-black/[0.04]`), toasts, shell (sidebar `bg-panel`, top bar blur-white) for light surfaces; rename every visible string, `layout.tsx` metadata, FastAPI title, README/demo-script names.
- [ ] **Step 3: Verify** — `npm test` PASS; `npx tsc --noEmit`; `grep -ri bhoomi frontend/src backend/app README.md docs/demo-script.md` → only allowed hit is none (0 lines). Run `npm run dev` + backend and eyeball `/app`, `/app/map`, `/app/conflicts`, `/app/analytics` in the browser at 1440px: readable, no dark remnants (screenshot each).
- [ ] **Step 4: Run old e2e** — `npx playwright test` — the 4 existing tests still pass (landing test still finds its links until Task 5 changes them; if the hero CTA text changes here, don't — CTA copy changes in Task 5 only).
- [ ] **Step 5: Commit** — `feat: rebrand to UrbanSync AI with premium light theme`

### Task 2: City registry, parametrized synthetic city, /cities API, second-city validation

**Files:**
- Create: `backend/app/cities.py`, `backend/app/validate.py`, `backend/app/api/cities.py`, `backend/tests/test_cities.py`
- Modify: `backend/app/synthetic.py` (accept `origin_lonlat`), `backend/app/config.py` (`demo_city: str = "pune"`, `validation_dir: Path = REPO/data/validation`), `backend/app/seed.py` (tag datasets with the demo city; call validation build if missing), `backend/app/main.py` (router), `.gitignore` (`data/validation/` stays generated → ignore it; it is rebuilt by seed)

**Interfaces:**
- `app/cities.py`: `CITIES: list[dict]` per the Global Constraints registry, each `{id, name, state, lon, lat, status}`; `get_city(id) -> dict | None`.
- `generate_ward(out_dir, seed=42, origin_lonlat=(73.8567, 18.5204)) -> dict` — default unchanged so the existing demo data stays byte-identical.
- `app/validate.py`: `validate_city(city_id: str, seed: int = 11) -> dict` — generates that city's ward in a temp dir, runs the **unchanged** `match_layers` + `detect_conflicts` against its ground truth, writes `data/validation/<city_id>.json` with `{city, seed, parcels, match_precision, match_recall, area_conflict_recall, owner_false_positive_rate, generated_at, label: "Synthetic validation dataset"}` and returns it. CLI `python -m app.validate` runs it for every `status=="validation"` city.
- `GET /cities` → `list[CityOut]`: `{id, name, state, coordinates: [lon, lat], status, dataset_type: "synthetic"|null, dataset_label, stats, test_area, validation}` where:
  - demo city: `dataset_label="Demo / Synthetic Dataset"`; `stats = {parcels, matched, conflicts_pending, conflicts_total, avg_confidence, last_run_at}` from live queries (`matched…avg_confidence` are **null** when no completed run — never invented); `test_area = {bbox: [..4], geometry: <cadastral footprint as 4326 GeoJSON>}` from the cadastral dataset footprint.
  - validation city: `dataset_label="Synthetic validation dataset"`, `validation` = the persisted JSON (null if absent), `stats/test_area` null.
  - planned: everything data-ish null.
- `GET /cities/{id}` → one CityOut, 404 for unknown.

- [ ] **Step 1: Write the failing tests** — `tests/test_cities.py`:

```python
def test_registry_has_eight_cities_one_demo_one_validation():
    assert len(CITIES) == 8
    assert [c["id"] for c in CITIES if c["status"] == "demo"] == ["pune"]
    assert [c["id"] for c in CITIES if c["status"] == "validation"] == ["surat"]

def test_generate_ward_origin_moves_city(tmp_path):
    generate_ward(tmp_path / "a", seed=11, origin_lonlat=(72.8311, 21.1702))
    b = gpd.read_file(tmp_path / "a" / "municipal.geojson").total_bounds
    assert 72.7 < b[0] < 72.95 and 21.0 < b[1] < 21.3

def test_default_demo_ward_unchanged(tmp_path, demo_dir):
    generate_ward(tmp_path)  # defaults
    assert (tmp_path / "ground_truth.json").read_bytes() == (demo_dir / "ground_truth.json").read_bytes()

def test_engine_is_city_agnostic(tmp_path):   # spec §35 — the same model on another city
    r = validate_city("surat", seed=11, out_dir=tmp_path)
    assert r["match_precision"] >= 0.97 and r["match_recall"] >= 0.97
    assert r["area_conflict_recall"] >= 0.9 and r["label"] == "Synthetic validation dataset"

def test_cities_endpoint_no_run_has_no_fake_stats(client, seeded):   # Review Focus 1
    cities = {c["id"]: c for c in client.get("/cities").json()}
    pune = cities["pune"]
    assert pune["status"] == "demo" and pune["stats"]["parcels"] == 1000
    assert pune["stats"]["matched"] is None and pune["stats"]["avg_confidence"] is None
    assert pune["test_area"]["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert cities["mumbai"]["stats"] is None and cities["mumbai"]["test_area"] is None

def test_cities_endpoint_after_run_uses_live_numbers(client, seeded):
    client.post("/harmonize")
    pune = client.get("/cities/pune").json()
    assert pune["stats"]["matched"] == 985 and 0.9 < pune["stats"]["avg_confidence"] < 0.98
    assert client.get("/cities/nowhere").status_code == 404
```
- [ ] **Step 2: Run, confirm FAIL** (ImportError). `validate_city` gains an `out_dir` kwarg for tests (defaults to `settings.validation_dir`).
- [ ] **Step 3: Implement** the five files/mods. `synthetic.py`: replace module-level `ORIGIN_LONLAT` use with the parameter (defaults preserve determinism). Seed: after ingest, if `settings.validation_dir` lacks `surat.json`, call `validate_city("surat")` (~5 s, once).
- [ ] **Step 4: Run** `uv run pytest -q` — all (old + new) pass. `curl -s localhost:8000/cities | python3 -m json.tool | head -30` shows pune with live stats after a run.
- [ ] **Step 5: Commit** — `feat: city registry, /cities API, city-parametrized ward, Surat validation run`

### Task 3: Vendor real India geography

**Files:**
- Create: `frontend/scripts/fetch-india-geo.mjs` (or a small python helper under `backend/` if easier with geopandas), `frontend/public/geo/india-states.json`, `frontend/public/geo/india-hero.json`
- Modify: `.gitignore` (ensure `public/geo/` **is committed** — it must not be regenerated at demo time), `README.md` (attribution)

**Interfaces:**
- `india-states.json`: FeatureCollection of Indian states/UTs (DataMeet Admin2 → simplified), each `properties.name`; EPSG:4326; **≤ 800 KB**; committed.
- `india-hero.json`: `{w, h, states: "<single SVG path d>", cities: [{id, name, x, y, status}]}` — equirectangular projection of the state outlines + the 8 registry cities, for the landing hero (same pattern as `hero/parcels.json`).
- Source: `https://raw.githubusercontent.com/datameet/maps/master/States/Admin2.geojson` (CC-BY 4.0; depicts India's official boundary). Fallback source if unreachable: geoBoundaries IND ADM1.

- [ ] **Step 1: Write the fetch/simplify script** (geopandas `simplify(0.02)` preserving topology per state is fine at this scale; round coords to 4 dp; write both artifacts).
- [ ] **Step 2: Run it once**; verify: `python3 -c` parse both files, `len(features) >= 33`, file sizes ≤ 800 KB / ≤ 200 KB; spot-check in a scratch HTML or by bounds `[68±1, 6.5±1, 97.5±1, 37.5±1]`.
- [ ] **Step 3: Commit the artifacts + script + attribution** — `feat: vendor simplified India state boundaries (DataMeet, CC-BY 4.0)`

### Task 4: India Map page + navigation restructure

**Files:**
- Create: `frontend/src/lib/cities.ts`, `frontend/src/components/india/{IndiaMap.tsx,CityCard.tsx}`, `frontend/src/app/app/india/page.tsx`
- Modify: `frontend/src/components/ui/Shell.tsx` (nav), `frontend/src/app/app/page.tsx` (Overview header links to India Map)

**Interfaces:**
- `lib/cities.ts`: `CityProfile` TS type mirroring `CityOut` (spec §30 fields); `STATIC_CITIES` fallback (names/coords/status only, no stats) used when `/cities` is unreachable so the map still renders with an offline banner.
- `IndiaMap` props: `{ cities: CityProfile[]; selected: string | null; onSelect(id: string | null): void; onExplore(): void }`. MapLibre, `interactive`, no external sources: background `#f2f1ec`; `geojson` source from `/geo/india-states.json` (fill `#f8f7f3` / line `#cfccc0`, hover-state fill `#f1efe7`); **DOM markers** per city (dot + name label; demo = filled `#0f766e` with a CSS pulse ring, validation = `#0f766e` outline, planned = `#94a3b8`), no glyph/symbol layers. Exposes `window.__indiaMap` for e2e. Behavior: initial `fitBounds([68, 6.5, 97.5, 37.5])`; select demo city → `flyTo` zoom 10.5 and add the `test_area` geometry as highlight layer (Global Constraints style) with a floating CTA **"Explore harmonized parcels"**; select planned/validation city → `flyTo` zoom 6.5 focus only. "Back to India" control re-fits. Load failure of `/geo/india-states.json` → `onStatus`-style error → page ErrorState + Retry (Review Focus 4).
- `CityCard` (hover + selected panel): demo → name, state, "Demo / Synthetic Dataset" badge, live stats (or "Run harmonization to see match stats" when null), `[Explore area]`; validation → "Synthetic validation dataset" + engine metrics from `validation`; planned → "Dataset not connected yet." + spec §33 body + `[View architecture]` (→ `/#architecture`) + "Request / add city dataset" (mailto-less button → toast "Noted — dataset onboarding is a planned integration"). Never renders numeric stats for planned cities (Review Focus 2).
- Page `/app/india`: left rail (search input filtering the 8 cities; result rows with ●/○ status dots; clicking = select; unknown query → "No city found — UrbanSync AI is designed to add more city datasets."), map fills the rest; `?city=` deep-link supported; header "India · 8 city profiles · 1 active demo dataset" (counts computed from `/cities`).
- Nav: sidebar order Overview `/app`, **India Map `/app/india`**, Web GIS `/app/map`, Data Sources, Harmonize, Conflicts, Analytics; sidebar footer block becomes "Demo Workspace" + existing scope note; mobile bottom nav shows 5: Overview, India, GIS, Conflicts, Analytics.

- [ ] **Step 1: Write failing vitest** — `src/lib/cities.test.ts`: `STATIC_CITIES` has 8 entries, exactly one `demo` (pune), one `validation` (surat), and none carry stats fields. Run → FAIL.
- [ ] **Step 2: Implement** lib + components + page + nav. Reuse `useApi`, `EmptyState/ErrorState`, `Panel`, existing map lifecycle patterns (ResizeObserver, cleanup).
- [ ] **Step 3: Verify in browser** (backend seeded + harmonized): `/app/india` renders India with 8 labelled markers; hover Pune → live 1,000/985/…/94.2% card; click → smooth zoom, test-area highlight visible, "Explore harmonized parcels" → `/app/map`; click Mumbai → planned messaging, no stats; search "Surat" → validation card with real engine metrics; deep-link `?city=mumbai` works; no console errors. Screenshot each state.
- [ ] **Step 4: `npx tsc --noEmit && npx eslint src && npm test`** — clean.
- [ ] **Step 5: Commit** — `feat: India map with city drill-down, test-area highlight, multi-city nav`

### Task 5: Landing page rebuild (India-first story)

**Files:**
- Create: `frontend/src/components/india/IndiaHero.tsx`, `frontend/src/components/landing/{Solving.tsx,UseCases.tsx,CityExpansion.tsx,TestedArea.tsx,Generalize.tsx}`
- Modify: `frontend/src/app/page.tsx`, `frontend/src/components/landing/{Hero.tsx,HowItWorks.tsx,Pillars.tsx→ retire or fold}`, `frontend/e2e/demo.spec.ts` (landing entry only)

**Interfaces / content (exact copy from Global Constraints + spec):**
- Section order on `/`: **Hero** (IndiaHero SVG: single states path, 8 city dots, animated dashed connection lines demo→4 nearest cities, pulsing Pune dot with "Demo dataset" chip; `prefers-reduced-motion` disables; fallback to a plain light panel if `india-hero.json` fetch fails) → **"What are we actually solving?"** (3 columns: Problem / UrbanSync AI / Result, spec §10 text verbatim incl. the Result quote) → **How it works** `id="how"` (6 steps: Connect · Normalize · Match · Validate · Explain · Harmonize, spec §19 one-liners) → **"See the system in action"** (left: live stats via `/cities` — city name, "Demo urban area", parcels/matched/conflicts/avg confidence, honest "run harmonization" placeholder when null; right: compact `GisMap` of the parcels with its existing error state; CTA "Open interactive map" → `/app/map`; **disclosure card** verbatim: "Demo dataset — The current demonstration uses controlled/synthetic urban data to validate the harmonization workflow. Additional city datasets can be plugged into the same architecture.") → **"Where UrbanSync AI can help"** (6 use-case cards, spec §11, numbered 01–06, phrased as use cases) → **"Expanding Across India's Cities"** (city status list from `/cities` with `STATIC_CITIES` fallback; ● Demo dataset available / ◐ Synthetic validation dataset / ○ Dataset integration planned; "More city datasets coming") → **"Built for more cities, not just one test area."** `id="architecture"` (spec §9 paragraph + CITY DATASET→…→CITY HARMONIZED LAYER pipeline) → **"Designed to generalize across cities"** (Pune → same engine → Surat validation metrics from `/cities` when present, labelled; planned list) → footer (disclaimer + DataMeet attribution + "Demonstrated with controlled test data.").
- Hero header keeps Logo + "Workspace" link; CTAs per Global Constraints.
- e2e change: the landing step of `full SIH demo loop` becomes: `goto "/"` → click link "Explore India Map" → expect URL `/app/india` → (drill-down covered in Task 8's new test; the loop then `goto("/app/sources")` as before).

- [ ] **Step 1: Build IndiaHero + sections** (retire the dark ParcelField from the hero; keep the file only if reused elsewhere, else delete).
- [ ] **Step 2: Update the landing e2e step**; run `npx playwright test` → all pass.
- [ ] **Step 3: Verify in browser** at 1440/768/375: order, copy, honest numbers, anchors `#how`/`#architecture`, hero fallback (block `/geo/india-hero.json` via devtools route → panel fallback, no blank). Screenshots.
- [ ] **Step 4: Lighthouse on prod build** (`npm run build && npx next start -p 3210`): performance ≥ 85, accessibility ≥ 90 on `/`.
- [ ] **Step 5: Commit** — `feat: India-first landing with problem story, use cases, city expansion`

### Task 6: Workspace pages on the light theme + Overview restructure

**Files:**
- Modify: `frontend/src/app/app/page.tsx` (Overview), `.../analytics/page.tsx`, `.../sources/page.tsx`, `.../harmonize/page.tsx`, `.../conflicts/page.tsx`, `frontend/src/components/parcel/*`, `frontend/src/components/conflicts/*`, `frontend/src/components/dashboard/*` (spot-fix light-theme contrast leftovers found in browser)

**Interfaces:**
- Overview header: eyebrow "Command Center", title stays product-true; a chip row under it — "India · 8 city profiles · 1 active demo dataset" (from `/cities`) linking to `/app/india`; map preview panel titled with the demo city name ("Pune — harmonized parcels (demo)"); KPI cards unchanged (live numbers).
- Every page keeps its API contract; only presentation and the demo-city labelling ("Demo / Synthetic Dataset" badge on Sources page header and parcel drawer footer line stays the legal disclaimer).
- Parcel GIS `/app/map`: light basemap colors from Task 1's `layers.ts`; a small breadcrumb chip "India / Pune / Demo ward" linking back to `/app/india`.

- [ ] **Step 1: Sweep each page in the browser** (seeded + harmonized) at 1440 and 375, fix contrast/border/hover leftovers; keep all `data-testid`s and copy strings the e2e uses.
- [ ] **Step 2: Verify** the conflict resolve flow and parcel drawer visually (screenshots); `npx tsc --noEmit && npx eslint src && npm test`; run the full old e2e suite → 4 pass.
- [ ] **Step 3: Commit** — `feat: light-theme workspace with India context and demo-city labelling`

### Task 7: Higgsfield hero asset (only after Tasks 1–6 are green)

**Files:**
- Create: `frontend/public/hero/india-editorial.jpg` (≤ 400 KB, 1920px) via the `higgsfield-generate` skill
- Modify: one landing section only (the "Where UrbanSync AI can help" band header or final CTA band) to use it as a restrained background (low opacity / masked), never replacing the India-map hero (spec §18)

**Interfaces:**
- Prompt (spec §28 Asset 1 verbatim): "Premium editorial aerial visualization of a dense Indian city integrated with a clean India map interface, subtle cadastral parcel geometry, urban planning grid, sophisticated light background, architectural visualization aesthetic, restrained teal spatial highlights, high-end enterprise geospatial technology, no text, no logos."
- Skip Asset 2 (motion) unless time remains after Task 8; the app must stay fast.

- [ ] **Step 1: Generate via `higgsfield-generate`**, compress to ≤ 400 KB, place, integrate in the one chosen band with `loading="lazy"`.
- [ ] **Step 2: Verify** Lighthouse performance stays ≥ 85; the image is decorative (`alt=""`), lazy, and absent-file-safe (conditional render).
- [ ] **Step 3: Commit** — `feat: Higgsfield editorial visual on landing (restrained, lazy)`
- Time-box: 30 min. If generation fails or credits block, ledger it and ship without the asset.

### Task 8: e2e for the new journey, docs, full verification

**Files:**
- Modify: `frontend/e2e/demo.spec.ts` (add tests), `docs/demo-script.md` (new journey + real numbers), `README.md` (UrbanSync AI story, city architecture, validation, how-to-run)

**Interfaces / new e2e tests:**

```ts
test("India map drill-down to parcels", async ({ page }) => {
  await page.goto("/app/india");
  await expect(page.getByText("8 city profiles")).toBeVisible();
  await page.getByRole("button", { name: /Pune/ }).click();        // DOM marker
  await expect(page.getByText("Demo / Synthetic Dataset")).toBeVisible();
  await page.getByRole("button", { name: "Explore harmonized parcels" }).click();
  await expect(page).toHaveURL(/\/app\/map/);
});

test("planned city is honest", async ({ page }) => {              // Review Focus 2
  await page.goto("/app/india?city=mumbai");
  await expect(page.getByText("Dataset not connected yet.")).toBeVisible();
  await expect(page.getByText(/Demo \/ Synthetic Dataset/)).toHaveCount(0);
  await page.getByRole("textbox", { name: /Search a city/i }).fill("Delhi");
  await expect(page.getByText("Dataset integration planned").first()).toBeVisible();
});

test("no BhoomiSync anywhere; UrbanSync titles", async ({ page }) => {   // Review Focus 5
  for (const p of ["/", "/app", "/app/india"]) {
    await page.goto(p);
    await expect(page).toHaveTitle(/UrbanSync AI/);
    expect(await page.locator("body").innerText()).not.toContain("BhoomiSync");
  }
});

test("India map with geo asset blocked shows error, not blank", async ({ page }) => {  // Review Focus 4
  await page.route("**/geo/india-states.json", (r) => r.abort());
  await page.goto("/app/india");
  await expect(page.getByText(/Could not load|Retry/).first()).toBeVisible();
});
```
Also extend the mobile no-h-scroll route list with `/app/india`.

- [ ] **Step 1: Write the tests and run them** — all must pass against the finished Tasks 1–6. Then RED-verify each honesty test can actually fail: temporarily rename the metadata title back to "BhoomiSync AI" → the title test fails → revert; temporarily render demo stats on the Mumbai card → the planned-city test fails → revert. Record both RED runs in the ledger.
- [ ] **Step 2: Update `docs/demo-script.md`** to the §40 journey (Landing → India map → Pune → tested area → parcels → conflict → resolve → analytics → validation story), every number re-read from the live API; update README (name, story, city architecture, `python -m app.validate`, attribution, unchanged run commands).
- [ ] **Step 3: Clean-slate final verification** (REQUIRED SUB-SKILL: superpowers:verification-before-completion): `docker compose down -v && up --wait`, seed, backend suite, vitest, tsc, eslint, prod build, full Playwright suite (8 tests), Lighthouse `/` perf ≥ 85 / a11y ≥ 90, manual §44 checklist 1–20 in the browser, console/log check, screenshots at 1440/768/375.
- [ ] **Step 4: Commit** — `test+docs: India journey e2e, demo script, README for UrbanSync AI`
- [ ] **Step 5: Final report** to the user in the spec §45 format, with real numbers and RED-verified evidence.

---

## Spec Coverage Map

| Spec §§ | Task |
|---|---|
| 1 rename everywhere | 1 (+8 gate) |
| 2–3, 10, 19 story/workflow/problem | 5 |
| 4–7, 15–16, 24 India map, drill-down, highlight | 3, 4 |
| 6, 8–9, 30–33, 36 multi-city arch, statuses, empty states, search | 2, 4, 5 |
| 11–12 use cases, no overclaiming | 5 (copy), 2 (honest nulls) |
| 13–14, 22–27, 41 light premium UI, workspace | 1, 6 |
| 17–18, 20–21 landing, hero-as-map, tested area, disclosure | 5 |
| 28 Higgsfield | 7 |
| 29 responsive | 5, 6, 8 |
| 34 real geography, local | 3 |
| 35 second-city validation | 2 |
| 37–38, 42–43 preserve MVP, priorities, no static mockups | Global Constraints, 1–6 ordering |
| 39–40, 44–45 success criteria, journey, verification, report | 8 |
