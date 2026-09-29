# BhoomiSync AI One-Day MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local, offline, deterministic demo. Dirty multi-source synthetic land data for one urban ward is ingested, CRS-normalized, spatially matched with explainable confidence, attribute-mapped, and checked for conflicts and topology issues. The result is shown in a cinematic Next.js + MapLibre Web GIS where one conflict can be resolved end to end.

**Architecture:** Monorepo with `backend/` (FastAPI on Python 3.12, managed by `uv`), `frontend/` (Next.js App Router, TypeScript, Tailwind) and PostGIS in Docker. The harmonization engine is a set of pure functions over GeoDataFrames in `backend/app/engine/`, so it can be tested without a database. `backend/app/pipeline.py` orchestrates the engine and persists results through SQLAlchemy + GeoAlchemy2. All geometry is stored in the project CRS **EPSG:32643** (UTM 43N, which covers the Pune demo ward) and served to the browser as EPSG:4326 GeoJSON.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, GeoPandas, Shapely 2, PyProj, pyogrio, SQLAlchemy 2, GeoAlchemy2, psycopg 3, rapidfuzz, pytest, httpx · Next.js 15, React 19, TypeScript, Tailwind v4, maplibre-gl, recharts, framer-motion, vitest, @playwright/test · Docker `postgis/postgis:16-3.4`.

**Spec:** [docs/prd.md](../../prd.md)

## Global Constraints

- Project CRS: `EPSG:32643`. Browser CRS: `EPSG:4326`. Use PyProj/GeoPandas `to_crs` only; never hand-rolled coordinate maths.
- Confidence weights (configurable in `backend/app/config.py`): geometry 0.30, centroid 0.20, area 0.15, shape/boundary 0.15, attribute 0.10, temporal 0.10.
- Match classes, exact strings: `HIGH` (label "High confidence", ≥ 0.85), `REVIEW` (0.60 – <0.85), `CONFLICT` (< 0.60).
- Conflict statuses, exact strings: `Pending Review`, `Accepted`, `Resolved`, `Ignored`.
- Conflict types, exact strings: `AREA_MISMATCH`, `OWNER_MISMATCH`, `DUPLICATE`, `BOUNDARY_OVERLAP`, `MISSING_ATTRIBUTE`, `SPATIAL_MISMATCH`, `TOPOLOGY`.
- Map colours: HIGH `#22c55e`, REVIEW `#f59e0b`, CONFLICT `#ef4444`, UNMATCHED `#64748b`. Accent `#2dd4bf` (teal). Shell background `#0a0c0f`, text `#e8eaed`.
- Canonical parcel IDs are `P1000`–`P1999`. Municipal IDs are `M7000`–`M7999` (a permuted, not id-aligned, mapping). Revenue Khasra numbers are `KH-<survey_no>`.
- Source records are immutable. Resolutions and suggested topology fixes are written to `canonical_parcels` / `topology_issues`, never to `source_features`.
- UI copy must never claim legal ownership determination. Wherever confidence is shown, the parcel drawer and conflict detail carry the footer "Decision-support only — not a legal determination of ownership."
- The demo must run with no internet. No basemap tiles by default: the map uses a blank dark style plus the synthetic roads layer. Fonts are self-hosted via `next/font`.
- All synthetic data is generated with `seed=42` and must be byte-identical across runs.
- Uploads: allowed extensions `.geojson`, `.json`, `.csv`, `.zip` (shapefile); max 20 MB. Uploaded files are parsed, never executed. Filenames and field names are sanitised to `[A-Za-z0-9_\-. ]`.
- DB credentials live only in `backend/.env`. The frontend only knows `NEXT_PUBLIC_API_URL`.
- Brand: **BhoomiSync AI**. Tagline: "One trusted spatial view of every urban parcel." Descriptor: "AI-powered multi-source land data harmonization."

## Review Focus

1. **An uploaded GeoJSON with no CRS, or a CSV whose "lat/lon" columns hold UTM metres or are swapped.** Expected: a 422 with a human-readable reason (e.g. "Coordinates out of range for EPSG:4326 — supply crs"), not features silently placed in the ocean. Pinned in Task 3.
2. **Running `POST /harmonize` twice, or while a run is still going.** Expected: the second call during a run gets 409. A second call after completion replaces the previous run's derived rows (no duplicate canonical parcels) and keeps the old run row as history. Pinned in Task 8.
3. **Resolving a conflict.** Expected: `source_features` rows are byte-for-byte unchanged, and the chosen value appears in `canonical_parcels.resolved_values` with a reviewer mark. Pinned in Task 9.
4. **A parcel with only one source, or a revenue point with no polygon.** Expected: confidence is computed from the available components with renormalised weights, missing components are reported as "not applicable", and no NaN reaches JSON. Pinned in Tasks 5 and 9.
5. **Backend down or empty database when the frontend loads.** Expected: every page shows an explicit error or empty state with a "Run harmonization" or "Retry" action, never a blank map or a crash. Pinned in Task 10 (unit) and Task 16 (e2e).

---

## File Structure

```
sih/
├── docker-compose.yml                 # PostGIS only
├── README.md                          # how to run + demo flow
├── docs/prd.md, docs/superpowers/plans/…
├── data/demo/                         # generated by `python -m app.synthetic` (git-ignored except .gitkeep)
├── backend/
│   ├── pyproject.toml, .env.example
│   ├── app/
│   │   ├── main.py                    # FastAPI app, CORS, router registration
│   │   ├── config.py                  # Settings (DATABASE_URL, PROJECT_CRS, DATA_DIR, WEIGHTS, thresholds)
│   │   ├── db.py                      # engine, SessionLocal, get_session, init_db()
│   │   ├── models.py                  # ORM tables (8 entities)
│   │   ├── schemas.py                 # Pydantic response models
│   │   ├── synthetic.py               # deterministic ward generator + ground truth
│   │   ├── seed.py                    # generate (if missing) + register + ingest demo datasets
│   │   ├── ingest/readers.py          # file → GeoDataFrame + detected CRS
│   │   ├── ingest/normalize.py        # CRS normalization + geometry validation report
│   │   ├── engine/attributes.py       # schema → canonical field mapping
│   │   ├── engine/matching.py         # candidates, component scores, confidence, class, explanation
│   │   ├── engine/conflicts.py        # conflict findings from matched records
│   │   ├── engine/topology.py         # invalid / self-intersection / overlap / gap
│   │   ├── engine/changes.py          # version A vs B diff
│   │   ├── pipeline.py                # run_harmonization(run_id) — stages persisted live
│   │   └── api/{datasets,harmonize,parcels,conflicts,layers,analytics}.py
│   └── tests/ (conftest.py + test_*.py per module)
└── frontend/
    ├── src/app/page.tsx               # landing
    ├── src/app/app/layout.tsx         # workspace shell (sidebar + top bar)
    ├── src/app/app/{page,sources,harmonize,map,conflicts,analytics}/…
    ├── src/components/{map,parcel,conflicts,dashboard,ui}/…
    ├── src/lib/{api.ts,types.ts,format.ts}
    ├── public/hero/ (hero.jpg, hero.webm optional)
    └── e2e/demo.spec.ts
```

---

### Task 1: Scaffold repo, PostGIS, backend health, frontend boot (Hour 0–1)

**Files:**
- Create: `.gitignore`, `docker-compose.yml`, `backend/pyproject.toml`, `backend/.env.example`, `backend/app/{__init__,main,config,db}.py`, `backend/tests/{__init__,conftest}.py`, `backend/tests/test_health.py`
- Create: `frontend/` via create-next-app

**Interfaces:**
- Produces: `app.main:app`. `app.config.settings` fields: `database_url: str`, `test_database_url: str`, `project_crs: str = "EPSG:32643"`, `data_dir: Path` (repo `data/demo`), `weights: dict[str, float]`, `high_threshold = 0.85`, `review_threshold = 0.60`, `cors_origins = ["http://localhost:3000"]`. `app.db`: `engine`, `SessionLocal`, `get_session()` FastAPI dependency, `init_db()` (runs `CREATE EXTENSION IF NOT EXISTS postgis` then `Base.metadata.create_all`), `Base` (DeclarativeBase).
- Produces for tests: the `conftest.py` fixture `db_session`, which points `settings.database_url` at `bhoomisync_test`, drops and recreates all tables per test module, and yields a Session. Also a `session_factory` fixture (a `sessionmaker` bound to the test engine, passed to `run_harmonization` in Task 8) and a `client` fixture (`fastapi.testclient.TestClient(app)` with `get_session` overridden to the test session).

- [ ] **Step 1: Init git and project skeleton**

```bash
cd /Users/vikasjadhav/Downloads/sih && git init && mkdir -p backend/app/{ingest,engine,api} backend/tests data/demo && touch data/demo/.gitkeep
```
`.gitignore`: `node_modules/`, `.next/`, `.venv/`, `__pycache__/`, `backend/.env`, `data/demo/*` with `!data/demo/.gitkeep`, `test-results/`, `playwright-report/`.

- [ ] **Step 2: docker-compose.yml**

Service `db`: image `postgis/postgis:16-3.4`, env `POSTGRES_USER=bhoomi`, `POSTGRES_PASSWORD=bhoomi`, `POSTGRES_DB=bhoomisync`, port `5433:5432` (avoids clashing with a local Postgres), named volume, healthcheck `pg_isready -U bhoomi`. Mount `./docker/init.sql`, which runs `CREATE DATABASE bhoomisync_test;`.

Run: `docker compose up -d && docker compose ps`. Expected: `db` is `healthy`.

- [ ] **Step 3: Backend project**

```bash
cd backend && uv init --python 3.12 --no-workspace --name bhoomisync-backend . && \
uv add fastapi "uvicorn[standard]" geopandas shapely pyproj pyogrio sqlalchemy geoalchemy2 "psycopg[binary]" rapidfuzz pydantic-settings python-multipart numpy pandas && \
uv add --dev pytest httpx
```
`.env.example`: `DATABASE_URL=postgresql+psycopg://bhoomi:bhoomi@localhost:5433/bhoomisync` and `TEST_DATABASE_URL=…/bhoomisync_test`. Copy it to `.env`.

- [ ] **Step 4: Write the failing test** — `backend/tests/test_health.py`

```python
def test_health_reports_db_and_postgis(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["postgis"].startswith("3.")
    assert body["project_crs"] == "EPSG:32643"
```

- [ ] **Step 5: Run it and confirm it fails.** Run: `cd backend && uv run pytest tests/test_health.py -v`. Expected: FAIL (ImportError: no `app.main`).

- [ ] **Step 6: Implement `config.py`, `db.py`, and `main.py` with `GET /health`.** `/health` runs `SELECT postgis_lib_version()`. If the DB is unreachable it still returns 200 with `database: "error"` so the frontend can show a banner. Add CORS middleware and call `init_db()` on startup (lifespan).

- [ ] **Step 7: Run the test and confirm it passes.** Then run `uv run uvicorn app.main:app --port 8000` and `curl -s localhost:8000/health`. Expected: JSON containing `"status":"ok"`.

- [ ] **Step 8: Frontend scaffold**

```bash
cd /Users/vikasjadhav/Downloads/sih && npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes && \
cd frontend && npm i maplibre-gl recharts framer-motion clsx && npm i -D vitest @vitejs/plugin-react jsdom @testing-library/react @playwright/test
```
Add `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`, and a `"test": "vitest run"` script.

Run: `npm run dev` and open `http://localhost:3000`. Expected: the default page renders (HTTP 200).

- [ ] **Step 9: Commit** — `git add -A && git commit -m "chore: scaffold backend, frontend, PostGIS"`

---

### Task 2: Deterministic synthetic ward + ground truth (Hour 1–2)

**Files:**
- Create: `backend/app/synthetic.py`, `backend/tests/test_synthetic.py`

**Interfaces:**
- Produces: `generate_ward(out_dir: Path, seed: int = 42) -> dict` returns a summary `{file_name: record_count}`. `python -m app.synthetic` writes to `settings.data_dir`. Files written, with CRS and schema:

| File | CRS | Geometry | Fields |
|---|---|---|---|
| `cadastral.geojson` | EPSG:32643 (GeoJSON `crs` member set) | Polygon ×1000 | `parcel_id` (P1000…), `survey_no` (int), `owner_name`, `area_sqm`, `land_use`, `survey_date` |
| `municipal.geojson` | EPSG:4326 | Polygon | `Property_ID`, `Owner`, `Area`, `Usage`, `Updated_On` |
| `municipal_v2.geojson` | EPSG:4326 | Polygon | same as municipal (next version, for change detection) |
| `revenue.csv` | lat/lon (4326) | Point | `Khasra_No`, `Owner_Name`, `Land_Area`, `Land_Type`, `latitude`, `longitude`, `Record_Date` |
| `buildings.geojson` | EPSG:4326 | Polygon ×~1500 | `building_id`, `floors`, `use` |
| `gnss.csv` | lat/lon | Point ×~300 | `survey_id`, `parcel_ref`, `accuracy_cm`, `lat`, `lon`, `observed_on` |
| `roads.geojson` | EPSG:4326 | LineString | `road_id`, `name`, `width_m` |
| `registered_sources.json` | — | ward bbox footprint | entries for Drone/ORI, DSM/DTM, Utilities: `{type, name, resolution, captured_on, crs, footprint}` |
| `ground_truth.json` | — | — | `{"matches": {municipal_id: parcel_id}, "injected": {defect_name: [parcel_id…]}, "changes": {"NEW": [...], "REMOVED": [...], "MODIFIED": [...]}}` |

- Layout: the ward origin is lon 73.8567, lat 18.5204, projected with pyproj to 32643. There are 25 blocks (5×5) of 40 parcels (2 rows × 20) at 15 m × 28 m (≈420 m²), with 12 m roads between blocks and ±0.4 m vertex jitter. Owners come from fixed lists of Indian first and last names. `land_use` ∈ {Residential, Commercial, Mixed Use, Institutional, Open Space}.
- Municipal = cadastral reprojected to 4326, shifted 0.2–1.5 m, with renamed fields. Inject exactly these counts and record each in `ground_truth.injected`: `area_mismatch` 60 (geometry scaled 1.07–1.15), `owner_variant` 50 (initials / reordered / case, e.g. "R. Sharma", "SHARMA RAHUL"; these must still match), `owner_different` 25, `duplicate` 15 (extra copy with a new ID, shifted ≤0.5 m), `missing_attribute` 30 (`Owner` or `Usage` null), `large_shift` 20 (6–12 m), `missing_in_municipal` 15.
- Cadastral defects: `invalid_geometry` 8 (bow-tie ring), `overlap` 12 (edge pushed 1.5 m into the neighbour), `gap` 10 (parcel shrunk 1 m on one side).
- Revenue: centroid ± 1 m. `Land_Type` values in upper case. 10 `area_mismatch` records overlap the municipal set.
- municipal_v2: 20 NEW, 10 REMOVED, 25 geometry-modified, 30 attribute-modified.

- [ ] **Step 1: Write the failing tests**

```python
def test_generate_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generate_ward(a); generate_ward(b)
    for f in ["cadastral.geojson", "municipal.geojson", "revenue.csv", "ground_truth.json"]:
        assert (a / f).read_bytes() == (b / f).read_bytes()

def test_counts_and_crs(tmp_path):
    summary = generate_ward(tmp_path)
    assert summary["cadastral.geojson"] == 1000
    assert 1400 <= summary["buildings.geojson"] <= 1600
    cad = gpd.read_file(tmp_path / "cadastral.geojson")
    assert cad.crs.to_epsg() == 32643
    assert gpd.read_file(tmp_path / "municipal.geojson").crs.to_epsg() == 4326
    assert cad["parcel_id"].iloc[0] == "P1000"

def test_ground_truth_injections(tmp_path):
    generate_ward(tmp_path)
    gt = json.loads((tmp_path / "ground_truth.json").read_text())
    assert len(gt["injected"]["area_mismatch"]) == 60
    assert len(gt["injected"]["invalid_geometry"]) == 8
    assert len(gt["matches"]) == 1000 - 15  # missing_in_municipal excluded, duplicates not in matches
    cad = gpd.read_file(tmp_path / "cadastral.geojson")
    assert (~cad.geometry.is_valid).sum() == 8
```

- [ ] **Step 2: Run the tests and confirm they fail.** `uv run pytest tests/test_synthetic.py -v`. Expected: ImportError.
- [ ] **Step 3: Implement `generate_ward`.** Use `numpy.random.default_rng(seed)` everywhere. Pick defect sets with `rng.choice(..., replace=False)` from disjoint pools so the counts stay exact. Write GeoJSON with `to_file(driver="GeoJSON", COORDINATE_PRECISION=7)` (2 for the 32643 file). Round CSV floats to 7 dp so the bytes are stable.
- [ ] **Step 4: Run the tests and confirm they pass.** Then run `uv run python -m app.synthetic`. Expected: it prints the summary and the files exist in `data/demo/`.
- [ ] **Step 5: Commit** — `feat: deterministic synthetic ward with injected discrepancies and ground truth`

---

### Task 3: DB models, ingestion, CRS normalization, datasets API (Hour 1–2)

**Files:**
- Create: `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/ingest/readers.py`, `backend/app/ingest/normalize.py`, `backend/app/seed.py`, `backend/app/api/datasets.py`
- Test: `backend/tests/test_ingest.py`, `backend/tests/test_datasets_api.py`

**Interfaces:**
- Consumes: `settings`, `Base`, `get_session` (Task 1); files from Task 2.
- Produces the ORM tables. All geometry columns are `Geometry(srid=32643)` via GeoAlchemy2 with a GiST index.
  - `Dataset`: `id`, `name`, `source_type` ∈ {`cadastral`,`municipal`,`revenue`,`buildings`,`gnss`,`roads`,`drone_ori`,`dsm_dtm`,`utilities`}, `version` (int, default 1), `file_name`, `source_crs`, `record_count`, `status` ∈ {`registered`,`ingested`,`processed`,`error`}, `fields` (JSON list), `metadata_` (JSON), `footprint` (geom, nullable), `last_processed` (datetime, nullable), `created_at`.
  - `SourceFeature`: `id`, `dataset_id` FK, `record_id` (str, the source's own id), `properties` (JSON, raw and never mutated), `geom`, `geom_valid` (bool).
  - `HarmonizationRun`: `id`, `status` ∈ {`running`,`completed`,`failed`}, `stages` (JSON list of `{key,label,status,started_at,finished_at,detail}`), `summary` (JSON), `started_at`, `finished_at`, `error`.
  - `AttributeMapping`: `id`, `run_id`, `dataset_id`, `source_field`, `canonical_field`, `confidence`, `method`.
  - `CanonicalParcel`: `id`, `run_id`, `parcel_id` (unique per run), `geom`, `area`, `owner_name`, `land_use`, `source_count`, `confidence_score`, `match_status` ∈ {`HARMONIZED`,`REVIEW`,`CONFLICT`,`UNMATCHED`}, `topology_status` ∈ {`VALID`,`ISSUE`,`SUGGESTED_FIX`}, `provenance` (JSON list `{source_type, dataset_id, source_feature_id, record_id}`), `resolved_values` (JSON dict `field → {value, source, resolved_by, resolved_at, note}`), `building_count`, `gnss_count`, `last_updated`.
  - `FeatureMatch`: `id`, `run_id`, `source_feature_id`, `target_feature_id` (the cadastral source feature), `canonical_parcel_id`, `geometry_score`, `centroid_score`, `area_score`, `shape_score`, `attribute_score`, `temporal_score` (all nullable float), `final_confidence`, `match_class`, `evidence` (JSON), `explanation` (text).
  - `Conflict`: `id`, `run_id`, `canonical_parcel_id`, `conflict_type`, `source_a`, `source_b`, `observed` (JSON `{a: value, b: value, delta}`), `confidence`, `explanation`, `recommended_action`, `status` (default `Pending Review`), `resolution` (JSON), `resolved_at`; relationship `parcel -> CanonicalParcel` (and `CanonicalParcel.conflicts` back-ref).
  - `TopologyIssue`: `id`, `run_id`, `canonical_parcel_id` (nullable), `issue_type` ∈ {`INVALID_GEOMETRY`,`SELF_INTERSECTION`,`OVERLAP`,`GAP`}, `geom` (issue location), `detail`, `suggested_fix` (geom, nullable), `fix_status` ∈ {`auto_safe`,`requires_review`}.
- `read_source(path: Path, crs_hint: str | None = None) -> tuple[gpd.GeoDataFrame, str]` returns (gdf, detected CRS as `"EPSG:xxxx"`). For CSV, lat/lon columns are auto-detected from the names {`lat`,`latitude`,`y`} and {`lon`,`lng`,`longitude`,`x`}. For `.zip`, it reads the first `.shp` inside via `pyogrio` with `vsizip`. Raises `IngestError(message: str)` on problems.
- `normalize(gdf, target_crs: str = settings.project_crs) -> NormalizeResult` (dataclass): `gdf` (in target CRS), `source_crs`, `target_crs`, `invalid_count`, `empty_count`.
- `ingest_file(session, path, source_type, name, crs_hint=None, version=1) -> Dataset` writes the Dataset and its SourceFeatures (record_id taken from the first id-like column: `parcel_id`, `Property_ID`, `Khasra_No`, `building_id`, `survey_id`, `road_id`; otherwise the row index).
- `seed_demo(session) -> list[Dataset]`: generates data if it is missing, then ingests the 7 vector files (municipal_v2 as `municipal` version 2) and registers the 3 raster-type sources with status `registered`. It is idempotent: it truncates the dataset tables first. CLI: `python -m app.seed`.
- API: `GET /datasets -> list[DatasetOut]` (fields: `id,name,source_type,version,record_count,source_crs,target_crs,status,last_processed,fields`). `POST /datasets/upload` is multipart with `file`, `source_type`, optional `crs`, and returns `DatasetOut` with status 201.

- [ ] **Step 1: Write the failing ingest tests** — `test_ingest.py`

```python
def test_geojson_32643_detected(demo_dir):
    gdf, crs = read_source(demo_dir / "cadastral.geojson")
    assert crs == "EPSG:32643" and len(gdf) == 1000

def test_csv_latlon_detected_and_normalized(demo_dir):
    gdf, crs = read_source(demo_dir / "revenue.csv")
    assert crs == "EPSG:4326"
    res = normalize(gdf)
    assert res.source_crs == "EPSG:4326" and res.target_crs == "EPSG:32643"
    x, y = res.gdf.geometry.iloc[0].x, res.gdf.geometry.iloc[0].y
    assert 350_000 < x < 400_000 and 2_030_000 < y < 2_070_000

def test_municipal_aligns_with_cadastral_after_normalize(demo_dir):
    cad = normalize(read_source(demo_dir / "cadastral.geojson")[0]).gdf
    mun = normalize(read_source(demo_dir / "municipal.geojson")[0]).gdf
    assert cad.total_bounds[0] == pytest.approx(mun.total_bounds[0], abs=20)

def test_csv_with_utm_values_as_latlon_rejected(tmp_path):   # Review Focus 1
    p = tmp_path / "bad.csv"; p.write_text("id,lat,lon\n1,2047900,373000\n")
    with pytest.raises(IngestError, match="out of range for EPSG:4326"):
        read_source(p)

def test_csv_without_coordinate_columns_rejected(tmp_path):
    p = tmp_path / "bad.csv"; p.write_text("id,name\n1,a\n")
    with pytest.raises(IngestError, match="latitude/longitude"):
        read_source(p)

def test_invalid_geometries_counted(demo_dir):
    assert normalize(read_source(demo_dir / "cadastral.geojson")[0]).invalid_count == 8
```
`demo_dir` is a session-scoped fixture in `conftest.py` that calls `generate_ward(tmp_path_factory.mktemp("demo"))`.

- [ ] **Step 2: Run the tests and confirm they fail.**
- [ ] **Step 3: Implement `readers.py` and `normalize.py`.** GeoJSON without a `crs` member is assumed to be 4326, but only if its bounds fall within ±180/±90; otherwise raise `IngestError("Coordinates out of range for EPSG:4326 — supply crs")`. Apply the same range check to CSV values. When a `crs_hint` is given, it overrides detection. `normalize` must not repair geometry; it only counts invalid and empty geometries.
- [ ] **Step 4: Run the ingest tests and confirm they pass.**
- [ ] **Step 5: Write the failing API tests** — `test_datasets_api.py`

```python
def test_seeded_datasets_listed(client, seeded):
    ds = client.get("/datasets").json()
    types = {d["source_type"] for d in ds}
    assert {"cadastral","municipal","revenue","buildings","gnss","drone_ori","dsm_dtm","utilities"} <= types
    cad = next(d for d in ds if d["source_type"] == "cadastral")
    assert cad["record_count"] == 1000 and cad["source_crs"] == "EPSG:32643"
    assert next(d for d in ds if d["source_type"] == "drone_ori")["status"] == "registered"

def test_upload_geojson(client, demo_dir):
    with open(demo_dir / "buildings.geojson", "rb") as f:
        r = client.post("/datasets/upload", files={"file": ("b.geojson", f)}, data={"source_type": "buildings"})
    assert r.status_code == 201 and r.json()["record_count"] > 1000

def test_upload_rejects_bad_extension(client, tmp_path):
    p = tmp_path / "x.exe"; p.write_bytes(b"MZ")
    r = client.post("/datasets/upload", files={"file": ("x.exe", p.open("rb"))}, data={"source_type": "cadastral"})
    assert r.status_code == 422 and "Unsupported file type" in r.json()["detail"]

def test_upload_bad_coords_is_422(client, tmp_path):
    p = tmp_path / "bad.csv"; p.write_text("id,lat,lon\n1,2047900,373000\n")
    r = client.post("/datasets/upload", files={"file": ("bad.csv", p.open("rb"))}, data={"source_type": "gnss"})
    assert r.status_code == 422 and "out of range" in r.json()["detail"]
```
The `seeded` fixture runs `seed_demo(db_session)` with `settings.data_dir` pointed at `demo_dir`.

- [ ] **Step 6: Run the API tests and confirm they fail.**
- [ ] **Step 7: Implement `models.py`, `schemas.py`, `seed.py`, and `api/datasets.py`.** The upload handler checks the extension allow-list and size (20 MB), writes to a temp dir under `data/uploads/` with a sanitised name, calls `ingest_file`, and maps `IngestError` to 422. Register the router in `main.py`.
- [ ] **Step 8: Run all backend tests and confirm they pass.** Then run `uv run python -m app.seed` followed by `curl -s localhost:8000/datasets | head -c 400`. Expected: 11 datasets, including municipal v2.
- [ ] **Step 9: Commit** — `feat: PostGIS models, ingestion with CRS detection/normalization, datasets API`

---

### Task 4: Intelligent attribute mapping (Hour 2–4)

**Files:**
- Create: `backend/app/engine/attributes.py`, `backend/tests/test_attributes.py`

**Interfaces:**
- Produces: `CANONICAL_FIELDS = ["parcel_id","source_property_id","owner_name","area","land_use","survey_date"]`. `@dataclass FieldMapping(source_field: str, canonical_field: str | None, confidence: float, method: Literal["synonym","fuzzy","value_profile","unmapped"])`.
- `map_fields(df: pd.DataFrame) -> list[FieldMapping]` skips geometry and lat/lon columns.
- `apply_mapping(df, mappings) -> pd.DataFrame` returns only the canonical columns. Values are normalised: `land_use` is title-cased, `area` becomes float, `owner_name` is whitespace-collapsed.
- `normalize_name(s: str | None) -> str` lowercases, strips punctuation, and sorts tokens.
- `name_similarity(a, b) -> float | None` (0–1) uses rapidfuzz `token_set_ratio` on normalised names and returns None if either is empty.
- Method: a synonym table gives confidence 0.95. Otherwise the best rapidfuzz `WRatio` of the field name against the synonyms, if ≥ 80, gives confidence `score/100 * 0.9`. As a tiebreak, value profiling raises confidence by 0.05 when the dtype fits (numeric → area; mostly-alphabetic names with 2+ tokens → owner_name; ≤10 distinct strings → land_use).

- [ ] **Step 1: Write the failing tests**

```python
REVENUE = pd.DataFrame({"Khasra_No": ["KH-104"], "Owner_Name": ["Rahul Sharma"], "Land_Area": [420.0], "Land_Type": ["RESIDENTIAL"]})
MUNICIPAL = pd.DataFrame({"Property_ID": ["M7781"], "Owner": ["R. Sharma"], "Area": [418.2], "Usage": ["Residential"]})

def as_dict(ms): return {m.source_field: m.canonical_field for m in ms}

def test_prd_revenue_mapping():
    assert as_dict(map_fields(REVENUE)) == {"Khasra_No": "parcel_id", "Owner_Name": "owner_name", "Land_Area": "area", "Land_Type": "land_use"}

def test_prd_municipal_mapping():
    assert as_dict(map_fields(MUNICIPAL)) == {"Property_ID": "source_property_id", "Owner": "owner_name", "Area": "area", "Usage": "land_use"}

def test_fuzzy_field_name_maps_with_lower_confidence():
    m = map_fields(pd.DataFrame({"OwnrName": ["A B"]}))[0]
    assert m.canonical_field == "owner_name" and m.method == "fuzzy" and m.confidence < 0.95

def test_unknown_field_unmapped():
    m = map_fields(pd.DataFrame({"zzz_flag": [1]}))[0]
    assert m.canonical_field is None and m.method == "unmapped"

def test_name_similarity():
    assert name_similarity("Rahul Sharma", "SHARMA RAHUL") == 1.0
    assert name_similarity("Rahul Sharma", "R. Sharma") >= 0.8
    assert name_similarity("Rahul Sharma", "Priya Deshmukh") < 0.5
    assert name_similarity("Rahul Sharma", None) is None

def test_apply_mapping_normalizes_values():
    out = apply_mapping(REVENUE, map_fields(REVENUE))
    assert out.loc[0, "land_use"] == "Residential" and out.loc[0, "area"] == 420.0
```

- [ ] **Step 2: Run the tests and confirm they fail.** `uv run pytest tests/test_attributes.py -v`
- [ ] **Step 3: Implement `attributes.py`.**
- [ ] **Step 4: Run the tests and confirm they pass.**
- [ ] **Step 5: Commit** — `feat: attribute mapping engine with confidence`

---

### Task 5: Spatial matching + explainable confidence (Hour 2–4, most important)

**Files:**
- Create: `backend/app/engine/matching.py`, `backend/tests/test_matching.py`

**Interfaces:**
- Consumes: `name_similarity` (Task 4), `settings.weights`, and the thresholds.
- Produces:
  - `@dataclass ScoreBreakdown(geometry: float|None, centroid: float|None, area: float|None, shape: float|None, attribute: float|None, temporal: float|None, final: float, match_class: str, evidence: dict)`. `evidence` keys: `iou`, `centroid_distance_m`, `area_diff_pct`, `hausdorff_m`, `name_similarity`, `date_gap_days`, `point_in_polygon` (each value or None).
  - `score_pair(base_geom, other_geom, base_attrs: dict, other_attrs: dict) -> ScoreBreakdown`. Geometries are in metres (EPSG:32643). Attrs are canonical dicts from `apply_mapping`.
  - Component formulas (each clipped to 0–1):
    - geometry = IoU; if `other` is a Point, 1.0 if it lies within `base`, else 0.0.
    - centroid = `exp(-d / 5.0)`.
    - area = `1 - |a1-a2| / max(a1,a2)`, using `other_attrs["area"]` when the other geometry is a Point.
    - shape = `exp(-hausdorff / 5.0)`, None for points.
    - attribute = `name_similarity`, None if either name is missing.
    - temporal = `max(0, 1 - days/3650)`, None if either date is missing.
  - `final` = Σ wᵢ·sᵢ over non-None components ÷ Σ wᵢ of those components. It is rounded to 4 dp and is never NaN.
  - `classify(final: float) -> Literal["HIGH","REVIEW","CONFLICT"]`
  - `explain(b: ScoreBreakdown, base_id: str, other_id: str, other_label: str) -> str` returns a multi-line string in PRD §11 style. Lines start with `✓` when the component is ≥ 0.8, `!` when < 0.6, and `·` otherwise. The last line is `Reason: …`, with one fixed sentence per class:
    - HIGH: "The two features represent the same spatial parcel with strong geometric and attribute agreement."
    - REVIEW: "Likely the same parcel, but some evidence disagrees — reviewer confirmation recommended."
    - CONFLICT: "Evidence is contradictory; manual review required before these records are linked."
  - `match_layers(base: gpd.GeoDataFrame, other: gpd.GeoDataFrame, base_id_col: str, other_id_col: str, max_distance_m: float = 15.0) -> list[Match]`, where `@dataclass Match(base_id, other_id, breakdown: ScoreBreakdown)`. Candidates come from `gpd.sjoin_nearest(max_distance=...)` plus `sindex.query(buffer)`. The assignment is one-to-one and greedy by descending `final`. Unassigned other-features that overlap an already-assigned base with IoU ≥ 0.8 are returned as `Match` objects with `evidence["duplicate_of"] = <other_id>` (these feed the DUPLICATE conflicts in Task 6).
  - `WEIGHTS` read from settings: `{"geometry":0.30,"centroid":0.20,"area":0.15,"shape":0.15,"attribute":0.10,"temporal":0.10}`.

- [ ] **Step 1: Write the failing tests**

```python
sq = lambda x0, y0, w=15, h=28: box(x0, y0, x0 + w, y0 + h)

def test_identical_parcels_high():
    b = score_pair(sq(0,0), sq(0,0), {"owner_name":"Rahul Sharma","area":420}, {"owner_name":"SHARMA RAHUL","area":420})
    assert b.final >= 0.95 and b.match_class == "HIGH"

def test_small_shift_still_high():
    b = score_pair(sq(0,0), sq(1.0,0.5), {"owner_name":"A B"}, {"owner_name":"A B"})
    assert b.match_class == "HIGH" and b.evidence["centroid_distance_m"] == pytest.approx(1.118, abs=0.01)

def test_area_mismatch_drops_to_review():
    b = score_pair(sq(0,0), scale(sq(0,0), 1.12, 1.12), {"owner_name":"A B"}, {"owner_name":"A B"})
    assert b.match_class == "REVIEW"

def test_far_different_owner_conflict():
    b = score_pair(sq(0,0), sq(10,8), {"owner_name":"Rahul Sharma"}, {"owner_name":"Priya Deshmukh"})
    assert b.match_class == "CONFLICT"

def test_missing_components_renormalized():            # Review Focus 4
    b = score_pair(sq(0,0), Point(7.5, 14), {"area": 420}, {"area": 420})
    assert b.geometry == 1.0 and b.shape is None and b.attribute is None and b.temporal is None
    assert not math.isnan(b.final) and b.final >= 0.85

def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)

def test_explanation_lists_evidence():
    b = score_pair(sq(0,0), sq(0.5,0), {"owner_name":"A B"}, {"owner_name":"A B"})
    text = explain(b, "P1023", "M7781", "Municipal")
    assert "P1023 ↔ Municipal M7781" in text and "overlap" in text and "Reason:" in text

def test_match_layers_one_to_one_and_duplicate(tmp_path):
    base = gpd.GeoDataFrame({"pid":["P1","P2"]}, geometry=[sq(0,0), sq(20,0)], crs=32643)
    other = gpd.GeoDataFrame({"mid":["M1","M2","M3"]}, geometry=[sq(0.5,0), sq(20.3,0), sq(0.2,0)], crs=32643)
    ms = match_layers(base, other, "pid", "mid")
    primary = [m for m in ms if "duplicate_of" not in m.breakdown.evidence]
    assert sorted((m.base_id, m.other_id) for m in primary) in ([("P1","M3"),("P2","M2")], [("P1","M1"),("P2","M2")])
    assert any("duplicate_of" in m.breakdown.evidence for m in ms)

def test_accuracy_against_ground_truth(demo_dir):
    # full synthetic ward: municipal vs cadastral
    cad = normalize(read_source(demo_dir/"cadastral.geojson")[0]).gdf
    mun = normalize(read_source(demo_dir/"municipal.geojson")[0]).gdf
    gt = json.loads((demo_dir/"ground_truth.json").read_text())["matches"]
    ms = [m for m in match_layers(cad, mun, "parcel_id", "Property_ID") if "duplicate_of" not in m.breakdown.evidence]
    correct = sum(gt.get(m.other_id) == m.base_id for m in ms)
    assert correct / len(gt) >= 0.97 and correct / len(ms) >= 0.97
```
`test_accuracy_against_ground_truth` needs attributes mapped before scoring. Inside `match_layers`, `base_attrs`/`other_attrs` come from `apply_mapping(map_fields(df))` computed once per layer.

- [ ] **Step 2: Run the tests and confirm they fail.**
- [ ] **Step 3: Implement `matching.py`.** Use `shapely.hausdorff_distance`. Compute IoU with `make_valid` applied to copies (never the input). Vectorise candidate generation; a per-pair Python loop is fine at ~3k pairs.
- [ ] **Step 4: Run the tests and confirm they pass.** Also time `test_accuracy_against_ground_truth`; it must be < 10 s. If it is slower, restrict candidates to the nearest 3 per base.
- [ ] **Step 5: Commit** — `feat: spatial matching engine with explainable weighted confidence`

---

### Task 6: Conflict detection + topology validation (Hour 2–4)

**Files:**
- Create: `backend/app/engine/conflicts.py`, `backend/app/engine/topology.py`, `backend/tests/test_conflicts.py`, `backend/tests/test_topology.py`

**Interfaces:**
- Consumes: `Match`, `ScoreBreakdown`, `name_similarity`.
- Produces:
  - `@dataclass ConflictFinding(parcel_id, conflict_type, source_a, source_b, observed: dict, confidence: float, explanation: str, recommended_action: str)`
  - `detect_conflicts(parcel_id: str, base_attrs: dict, matches: dict[str, Match | None], other_attrs: dict[str, dict]) -> list[ConflictFinding]`. The `matches` keys are source types (`municipal`, `revenue`). The rules:
    - `AREA_MISMATCH` when area_diff_pct > 5.0. Explanation: "Area differs by {x:.1f}%." Action: "Verify with field survey; prefer GNSS-backed area."
    - `OWNER_MISMATCH` when name_similarity < 0.6. Action: "Manual review required — confirm with revenue record."
    - `MISSING_ATTRIBUTE` when owner_name or land_use is null in a matched source. Action: "Backfill from highest-confidence source (suggested)."
    - `SPATIAL_MISMATCH` when a polygon match has IoU < 0.75. Explanation includes "overlap by only {iou:.0%}". Action: "Manual review required."
    - `DUPLICATE` when the match evidence has `duplicate_of`. Action: "Retain one record; mark the other as duplicate."
    - `confidence` = the detector's certainty: for area it is `min(1, pct/15)` floored at 0.6; for owner it is `1 - similarity`; others are fixed at 0.9.
  - `@dataclass TopologyFinding(parcel_id: str|None, issue_type, location: BaseGeometry, detail: str, suggested_fix: BaseGeometry|None, fix_status: Literal["auto_safe","requires_review"])`
  - `validate_topology(gdf: gpd.GeoDataFrame, id_col: str, min_overlap_sqm: float = 0.5, max_gap_sqm: float = 200.0) -> list[TopologyFinding]`:
    - invalid geometry → `SELF_INTERSECTION` if `explain_validity` contains "Self-intersection", else `INVALID_GEOMETRY`. The suggested fix is `make_valid` → largest polygon, with fix_status `auto_safe` only if the fixed area is within 1% of the original ring's shoelace area; otherwise `requires_review`.
    - pairwise overlaps via `sindex.query(predicate="intersects")` with intersection area > min_overlap_sqm → `OVERLAP` with `requires_review` (no auto-fix).
    - gaps = interior rings of `unary_union(valid parcels)` with area in (1, max_gap_sqm] → `GAP`, parcel_id None, `requires_review`.
  - Detail text for requires_review findings ends with "Correction suggested — requires review."

- [ ] **Step 1: Write the failing tests**

```python
def test_area_mismatch_flagged_with_pct():
    m = Match("P1", "M1", score_pair(sq(0,0), scale(sq(0,0), 1.1, 1.0), {}, {}))
    fs = detect_conflicts("P1", {"owner_name":"A B","land_use":"Residential"}, {"municipal": m}, {"municipal":{"owner_name":"A B","land_use":"Residential"}})
    f = next(f for f in fs if f.conflict_type == "AREA_MISMATCH")
    assert "Area differs by" in f.explanation and f.source_a == "cadastral" and f.source_b == "municipal"

def test_owner_variant_not_conflict():
    m = Match("P1","M1", score_pair(sq(0,0), sq(0,0), {"owner_name":"Rahul Sharma"}, {"owner_name":"R. Sharma"}))
    fs = detect_conflicts("P1", {"owner_name":"Rahul Sharma","land_use":"Residential"}, {"municipal": m}, {"municipal":{"owner_name":"R. Sharma","land_use":"Residential"}})
    assert not any(f.conflict_type == "OWNER_MISMATCH" for f in fs)

def test_missing_attribute_flagged(): ...        # municipal owner_name None → MISSING_ATTRIBUTE, observed["b"] is None
def test_clean_match_has_no_conflicts(): ...     # identical geom + attrs → []

def test_bowtie_self_intersection_suggested_fix():
    bow = Polygon([(0,0),(10,10),(10,0),(0,10)])
    fs = validate_topology(gpd.GeoDataFrame({"pid":["P1"]}, geometry=[bow], crs=32643), "pid")
    f = fs[0]
    assert f.issue_type == "SELF_INTERSECTION" and f.suggested_fix.is_valid and f.fix_status == "requires_review"

def test_overlap_detected():
    g = gpd.GeoDataFrame({"pid":["P1","P2"]}, geometry=[box(0,0,10,10), box(8.5,0,20,10)], crs=32643)
    f = next(f for f in validate_topology(g, "pid") if f.issue_type == "OVERLAP")
    assert f.location.area == pytest.approx(15.0) and "requires review" in f.detail

def test_gap_detected(): ...  # 3x3 grid of 10m boxes with the centre one shrunk by 1m on one side → one GAP of ~10 m²

def test_synthetic_ward_topology_counts(demo_dir):
    cad = normalize(read_source(demo_dir/"cadastral.geojson")[0]).gdf
    fs = validate_topology(cad, "parcel_id")
    assert sum(f.issue_type in ("SELF_INTERSECTION","INVALID_GEOMETRY") for f in fs) == 8
    assert sum(f.issue_type == "OVERLAP" for f in fs) >= 12
    assert sum(f.issue_type == "GAP" for f in fs) >= 10
```
The implementer writes the three `...` tests with exactly the assertion stated in each comment.

- [ ] **Step 2: Run the tests and confirm they fail.**
- [ ] **Step 3: Implement `conflicts.py` and `topology.py`.** The input GeoDataFrame is never modified; copy it before any `make_valid`.
- [ ] **Step 4: Run the tests and confirm they pass.**
- [ ] **Step 5: Commit** — `feat: conflict detection and topology validation with review-gated fixes`

---

### Task 7: Change detection (Hour 2–4, deterministic)

**Files:**
- Create: `backend/app/engine/changes.py`, `backend/tests/test_changes.py`

**Interfaces:**
- Produces: `@dataclass ChangeRecord(record_id: str, change: Literal["NEW","MODIFIED","REMOVED","UNCHANGED"], geometry_changed: bool, changed_fields: list[str], iou: float|None, geom: BaseGeometry)`.
- `detect_changes(a: gpd.GeoDataFrame, b: gpd.GeoDataFrame, id_col: str, iou_threshold: float = 0.95) -> list[ChangeRecord]`. Records are joined on `id_col`. A geometry change means IoU < threshold. `changed_fields` compares non-geometry columns with NaN treated as equal to None. `geom` comes from `b`, or from `a` for REMOVED records.

- [ ] **Step 1: Write the failing test** that pins this against ground truth:

```python
def test_changes_match_ground_truth(demo_dir):
    a = normalize(read_source(demo_dir/"municipal.geojson")[0]).gdf
    b = normalize(read_source(demo_dir/"municipal_v2.geojson")[0]).gdf
    gt = json.loads((demo_dir/"ground_truth.json").read_text())["changes"]
    rs = {r.record_id: r for r in detect_changes(a, b, "Property_ID")}
    assert {k for k, r in rs.items() if r.change == "NEW"} == set(gt["NEW"])
    assert {k for k, r in rs.items() if r.change == "REMOVED"} == set(gt["REMOVED"])
    assert {k for k, r in rs.items() if r.change == "MODIFIED"} == set(gt["MODIFIED"])
```
- [ ] **Step 2: Run the test and confirm it fails.** Then implement, run the test and confirm it passes, and commit: `feat: deterministic version change detection`.

---

### Task 8: Harmonization pipeline + run API (Hour 2–4)

**Files:**
- Create: `backend/app/pipeline.py`, `backend/app/api/harmonize.py`, `backend/tests/test_pipeline.py`

**Interfaces:**
- Consumes: Tasks 3–7.
- Produces:
  - `STAGES = [("ingest","Ingest"),("normalize","Normalize CRS"),("match","Spatial match"),("attributes","Map attributes"),("validate","Validate topology"),("resolve","Detect conflicts"),("harmonize","Harmonize")]`, the PRD §10.4 order. (The `resolve` key is kept so the UI shows "RESOLVE"; its work is conflict detection.)
  - `start_run(session) -> HarmonizationRun` raises `RunInProgress` if any run is `running`.
  - `run_harmonization(run_id: int, session_factory=SessionLocal) -> None` runs in a FastAPI `BackgroundTasks` worker and commits after every stage. For each stage it sets `status` `running`→`done` with timestamps and a truthful `detail`:
    - ingest: "11 datasets · 5,812 features" (real counts)
    - normalize: "EPSG:4326 → EPSG:32643 (4 datasets), EPSG:32643 native (3) · 8 invalid geometries"
    - match: "985 municipal, 1000 revenue matched"
    - and so on for the remaining stages.
  - Before writing, it deletes derived rows (`canonical_parcels`, `feature_matches`, `conflicts`, `topology_issues`, `attribute_mappings`) from previous runs. Old `harmonization_runs` rows are kept.
  - Canonical parcel build:
    - Base = cadastral (latest version). Matched against municipal (latest version) and revenue.
    - GNSS and buildings are spatially joined for `gnss_count`, `building_count` and provenance.
    - Canonical `area` = the cadastral geometry area. `owner_name`/`land_use` come from the highest-confidence source that has a non-null value.
    - `confidence_score` = mean `final` over the parcel's polygon and point matches.
    - `match_status`: `UNMATCHED` if there is no municipal or revenue match; otherwise the worst of `classify(confidence)` mapped to HIGH→`HARMONIZED`, REVIEW→`REVIEW`, CONFLICT→`CONFLICT`. Any pending conflict of type AREA/OWNER/SPATIAL/DUPLICATE caps the status at `REVIEW`.
    - The canonical geometry is the cadastral geometry. If topology has an `auto_safe` fix, the fixed geometry is used and `topology_status="SUGGESTED_FIX"`. Otherwise it uses `ISSUE` or `VALID`. The source row is untouched.
    - Topology findings become one `Conflict` of type `TOPOLOGY` per affected parcel so they appear in the Conflict Center.
  - Change detection runs on municipal v1 → v2 and is stored in `run.summary["changes"]` as a count per class. The records are recomputed on demand by `GET /layers/changes` (Task 9).
  - `run.summary` keys: `datasets`, `features`, `parcels`, `matched`, `high`, `review`, `conflict_class`, `unmatched`, `conflicts`, `topology_issues`, `avg_confidence`, `crs_transforms` (list of `{dataset, from, to}`), `changes`, `duration_s`.
- API:
  - `POST /harmonize` → 202 `{run_id}`, or 409 `{"detail":"A harmonization run is already in progress"}`.
  - `GET /harmonization/{run_id}` → `RunOut {id,status,stages,summary,started_at,finished_at,error}`.
  - `GET /harmonization/latest` → the latest RunOut, or 404.
  - On an exception the run gets `status=failed`, the error message is stored, and the current stage is marked `failed`.

- [ ] **Step 1: Write the failing tests** — `test_pipeline.py` (uses `seeded`; calls `run_harmonization` synchronously with the test session factory)

```python
def test_full_run_summary(db_session, seeded, session_factory):
    run = start_run(db_session); run_harmonization(run.id, session_factory)
    db_session.refresh(run)
    assert run.status == "completed" and [s["status"] for s in run.stages] == ["done"] * 7
    s = run.summary
    assert s["parcels"] == 1000 and s["matched"] >= 970
    assert 0.80 <= s["avg_confidence"] <= 0.98
    assert s["conflicts"] > 0 and s["topology_issues"] >= 30
    assert {"dataset": "municipal", "from": "EPSG:4326", "to": "EPSG:32643"} in s["crs_transforms"]

def test_conflict_detection_recall_vs_ground_truth(db_session, seeded, session_factory, demo_dir):
    run = start_run(db_session); run_harmonization(run.id, session_factory)
    gt = json.loads((demo_dir/"ground_truth.json").read_text())["injected"]
    flagged = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="AREA_MISMATCH")}
    assert len(flagged & set(gt["area_mismatch"])) / len(gt["area_mismatch"]) >= 0.9
    owner_variant_flagged = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="OWNER_MISMATCH")} & set(gt["owner_variant"])
    assert len(owner_variant_flagged) <= 3   # name variants must not be treated as conflicts

def test_provenance_kept(db_session, seeded, session_factory):
    run = start_run(db_session); run_harmonization(run.id, session_factory)
    p = db_session.query(CanonicalParcel).filter_by(parcel_id="P1023").one()
    assert {"cadastral","revenue"} <= {x["source_type"] for x in p.provenance}

def test_rerun_replaces_derived_rows(db_session, seeded, session_factory):       # Review Focus 2
    for _ in range(2):
        r = start_run(db_session); run_harmonization(r.id, session_factory)
    assert db_session.query(CanonicalParcel).count() == 1000
    assert db_session.query(HarmonizationRun).count() == 2

def test_concurrent_run_rejected(client, db_session, seeded):
    db_session.add(HarmonizationRun(status="running", stages=[], summary={})); db_session.commit()
    assert client.post("/harmonize").status_code == 409

def test_run_endpoint_shape(client, seeded):
    rid = client.post("/harmonize").json()["run_id"]   # TestClient runs background tasks before returning
    body = client.get(f"/harmonization/{rid}").json()
    assert body["status"] == "completed" and [s["key"] for s in body["stages"]][0] == "ingest"
```

- [ ] **Step 2: Run the tests and confirm they fail.**
- [ ] **Step 3: Implement `pipeline.py` and `api/harmonize.py`.** Persist geometries with `from_shapely(geom, srid=32643)`. Bulk-insert with `session.add_all`. The end-to-end run must be < 30 s.
- [ ] **Step 4: Run the tests and confirm they pass.** Then do a manual check: `curl -XPOST localhost:8000/harmonize` and poll `/harmonization/latest` until `completed`. Record the real numbers (matched, conflicts, avg confidence); they replace the PRD's example numbers everywhere in the demo script.
- [ ] **Step 5: Commit** — `feat: harmonization pipeline with persisted live stages`

---

### Task 9: Read APIs — parcels, conflicts + resolve, layers, analytics (Hour 2–4)

**Files:**
- Create: `backend/app/api/{parcels,conflicts,layers,analytics}.py`
- Modify: `backend/app/schemas.py`, `backend/app/main.py`
- Test: `backend/tests/test_read_api.py`

**Interfaces:**
- All geometry is returned as EPSG:4326 GeoJSON via `ST_AsGeoJSON(ST_Transform(geom, 4326), 7)` (7 decimal places ≈ 1 cm), and simplified with `ST_SimplifyPreserveTopology(geom, 0.2)` for layer endpoints.
- `GET /parcels?q=&status=&limit=50` → `list[ParcelSummary {parcel_id, owner_name, area, land_use, confidence_score, match_status, topology_status, source_count, conflict_count, bbox: [minx,miny,maxx,maxy]}]`. `q` matches parcel_id, owner name (ILIKE), municipal ID, or Khasra number (via provenance record_id).
- `GET /parcels/{parcel_id}` → `ParcelDetail`: the summary plus `geometry`, `provenance[]` (each with source label, record_id, dataset name, CRS), `matches[] {source_type, record_id, components: {geometry, centroid, area, shape, attribute, temporal} (null = not applicable), final_confidence, match_class, evidence, explanation}`, `source_values: {cadastral: {...canonical fields}, municipal: {...}, revenue: {...}}`, `conflicts[]`, `topology[]`, `resolved_values`, and `disclaimer` = the global disclaimer string. Returns 404 for an unknown ID.
- `GET /conflicts?type=&status=&limit=500` → `list[ConflictOut {id, parcel_id, conflict_type, source_a, source_b, observed, confidence, explanation, recommended_action, status, bbox}]`. `type` also accepts the UI filter aliases `area`→AREA_MISMATCH, `boundary`→{SPATIAL_MISMATCH, BOUNDARY_OVERLAP}, `attribute`→{OWNER_MISMATCH, MISSING_ATTRIBUTE}, `duplicate`→DUPLICATE, `topology`→TOPOLOGY.
- `GET /conflicts/{id}` → ConflictOut plus `source_values` for both sides.
- `POST /conflicts/{id}/resolve` takes body `{status: "Accepted"|"Resolved"|"Ignored", chosen_source?: str, field?: str, note?: str}`. It sets the status and `resolution`. For `Resolved` with a `chosen_source`, it writes `canonical_parcels.resolved_values[field] = {value, source, resolved_by: "reviewer", resolved_at, note}` and updates the canonical field. It then recomputes `match_status`: if no conflicts remain Pending Review, the parcel becomes `HARMONIZED`. It returns the updated ParcelDetail. A 422 is returned if `Resolved` lacks `chosen_source` for a value conflict.
- `GET /layers/{layer}` with layer ∈ {`parcels`, `municipal`, `revenue`, `buildings`, `gnss`, `roads`, `topology`, `conflicts`, `changes`} returns a FeatureCollection. Properties include `parcel_id`, `match_status`, `confidence_score` for parcels, and `change` for changes. An unknown layer returns 404.
- `GET /analytics` → `{kpis:{datasets, parcels, matched, high, review, conflict_class, unmatched, conflicts_pending, conflicts_resolved, topology_issues, avg_confidence, last_run_at}, match_distribution:[{class,count}], confidence_histogram:[{bin:"0.5–0.6",count}], conflict_breakdown:[{type,count}], topology_stats:[{type,count}], quality_before_after:[{metric, before, after}], evaluation:{match_precision, match_recall, area_conflict_recall, owner_false_positive_rate}, run: RunOut}`.
  - `quality_before_after` rows:
    - "Distinct CRS": before = count of distinct source CRSs, after = 1.
    - "Schemas / field names for owner": before = the number of distinct source fields mapped to owner_name, after = 1.
    - "Parcels with cross-source link": before = 0, after = matched.
    - "Invalid geometries": before = 8, after = the number of invalid geometries remaining unfixed.
    - "Unreviewed discrepancies": before = the number of conflicts found, after = pending.
  - `evaluation` is computed against `ground_truth.json` when the file is present. It is labelled "Evaluated on synthetic ground truth" in the UI.

- [ ] **Step 1: Write the failing tests** (module fixture: seed + one completed run)

```python
def test_parcel_detail_explainable(client):
    d = client.get("/parcels/P1023").json()
    assert d["parcel_id"] == "P1023" and d["geometry"]["type"] == "Polygon"
    m = d["matches"][0]
    assert set(m["components"]) == {"geometry","centroid","area","shape","attribute","temporal"}
    assert "Reason:" in m["explanation"] and "not a legal determination" in d["disclaimer"]

def test_no_nan_in_json(client):                                   # Review Focus 4
    txt = client.get("/layers/parcels").text
    assert "NaN" not in txt and "Infinity" not in txt

def test_search_by_owner_and_khasra(client):
    assert client.get("/parcels", params={"q": "P1023"}).json()[0]["parcel_id"] == "P1023"
    assert len(client.get("/parcels", params={"q": "KH-"}).json()) > 0

def test_conflict_filter_alias(client):
    rows = client.get("/conflicts", params={"type": "attribute"}).json()
    assert rows and {r["conflict_type"] for r in rows} <= {"OWNER_MISMATCH","MISSING_ATTRIBUTE"}

def test_resolve_updates_canonical_not_source(client, db_session):   # Review Focus 3
    c = client.get("/conflicts", params={"type": "area"}).json()[0]
    before = [(f.id, json.dumps(f.properties, sort_keys=True), f.geom.desc) for f in db_session.query(SourceFeature)]
    r = client.post(f"/conflicts/{c['id']}/resolve", json={"status": "Resolved", "chosen_source": "cadastral", "field": "area", "note": "GNSS confirms"})
    assert r.status_code == 200
    assert r.json()["resolved_values"]["area"]["resolved_by"] == "reviewer"
    db_session.expire_all()
    after = [(f.id, json.dumps(f.properties, sort_keys=True), f.geom.desc) for f in db_session.query(SourceFeature)]
    assert before == after
    assert client.get(f"/conflicts/{c['id']}").json()["status"] == "Resolved"

def test_resolve_value_conflict_requires_source(client):
    c = client.get("/conflicts", params={"type": "area", "status": "Pending Review"}).json()[0]
    assert client.post(f"/conflicts/{c['id']}/resolve", json={"status": "Resolved"}).status_code == 422

def test_layers(client):
    for layer in ["parcels","municipal","revenue","buildings","gnss","roads","topology","conflicts","changes"]:
        fc = client.get(f"/layers/{layer}").json()
        assert fc["type"] == "FeatureCollection" and fc["features"], layer
    assert client.get("/layers/nope").status_code == 404
    ch = {f["properties"]["change"] for f in client.get("/layers/changes").json()["features"]}
    assert {"NEW","MODIFIED","REMOVED"} <= ch

def test_analytics(client):
    a = client.get("/analytics").json()
    assert a["kpis"]["parcels"] == 1000 and a["evaluation"]["match_precision"] >= 0.97
    assert any(r["metric"] == "Distinct CRS" and r["after"] == 1 for r in a["quality_before_after"])

def test_unknown_parcel_404(client):
    assert client.get("/parcels/P9999").status_code == 404
```

- [ ] **Step 2: Run the tests and confirm they fail.**
- [ ] **Step 3: Implement the four routers and register them.** Serialise floats with a `clean()` helper that maps NaN/inf to None. Precompute each parcel's `bbox` via `ST_Extent` in the query.
- [ ] **Step 4: Run the full backend suite and confirm it passes.** `uv run pytest -q`. Expected: all tests pass. Check payload size: `curl -s localhost:8000/layers/parcels | wc -c` must be < 1.5 MB.
- [ ] **Step 5: Commit** — `feat: parcels, conflicts+resolve, layers, analytics APIs`

---

### Task 10: Frontend shell, design system, API client, states (Hour 4–5)

**Files:**
- Create: `frontend/src/lib/{api.ts,types.ts,format.ts}`, `frontend/src/lib/format.test.ts`, `frontend/src/lib/api.test.ts`
- Create: `frontend/src/app/app/layout.tsx`, `frontend/src/components/ui/{Panel,Kpi,StatusPill,EmptyState,ErrorState,Skeleton,Toast}.tsx`, `frontend/src/components/ui/Sidebar.tsx`
- Modify: `frontend/src/app/globals.css`, `frontend/src/app/layout.tsx`, `frontend/vitest.config.ts`

**Interfaces:**
- `types.ts` mirrors the backend schemas: `Dataset`, `Run`, `Stage`, `ParcelSummary`, `ParcelDetail`, `MatchOut`, `ConflictOut`, `Analytics`, `MatchStatus = "HARMONIZED"|"REVIEW"|"CONFLICT"|"UNMATCHED"`, `ConflictStatus`.
- `api.ts`: `apiGet<T>(path: string): Promise<T>`, `apiPost<T>(path, body?)`, `apiUpload(file: File, sourceType: string, crs?: string)`. Each throws `ApiError {status, message}`, with `message` taken from `detail` or, on a network failure, set to "Backend unreachable at <url>". There are also `useApi<T>(path: string | null) -> {data, error, loading, reload}` (a minimal hook, no SWR dependency) and `pollRun(runId, onUpdate) -> () => void` (1 s interval, stops on completed/failed).
- `format.ts`: `statusColor(s: MatchStatus) -> string` (the hex values from Global Constraints), `pct(x: number|null) -> string` ("—" for null), `classLabel(c) -> "High confidence"|"Review"|"Conflict"|"Unmatched"`, `conflictTypeLabel(t) -> string` (e.g. `AREA_MISMATCH` → "Area mismatch"), `fmtArea(m2) -> "420 m²"`.
- Design tokens as CSS variables in `globals.css`: `--bg #0a0c0f`, `--panel #11151a`, `--line rgba(255,255,255,.08)`, `--text #e8eaed`, `--muted #8b95a1`, `--accent #2dd4bf`, and the status colours. Fonts via `next/font/google` (downloaded at build, so they work offline at runtime): **Space Grotesk** for headings and **JetBrains Mono** for micro-labels. A subtle grid background (a CSS `background-image` linear-gradient at 32 px, 3% opacity) is used only on the shell.
- The workspace layout has a left sidebar with the routes Command Center `/app`, Data Sources `/app/sources`, Harmonize `/app/harmonize`, Web GIS `/app/map`, Conflicts `/app/conflicts`, Analytics `/app/analytics`. The top bar shows the last run status and a health dot from `/health`. When the backend is unreachable, a red banner appears: "Backend offline — start it with `uv run uvicorn app.main:app`" with a Retry button. The sidebar collapses to icons below 1024 px and becomes a bottom nav below 640 px.

- [ ] **Step 1: Write the failing unit tests**

```ts
test("statusColor", () => { expect(statusColor("HARMONIZED")).toBe("#22c55e"); expect(statusColor("CONFLICT")).toBe("#ef4444"); });
test("pct handles null", () => { expect(pct(0.934)).toBe("93%"); expect(pct(null)).toBe("—"); });
test("conflict labels", () => { expect(conflictTypeLabel("AREA_MISMATCH")).toBe("Area mismatch"); });
test("api surfaces unreachable backend", async () => {             // Review Focus 5
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));
  await expect(apiGet("/datasets")).rejects.toMatchObject({ message: expect.stringContaining("Backend unreachable") });
});
test("api surfaces 422 detail", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Unsupported file type" }), { status: 422 })));
  await expect(apiGet("/x")).rejects.toMatchObject({ status: 422, message: "Unsupported file type" });
});
```
- [ ] **Step 2: Run the tests and confirm they fail.** `cd frontend && npm test`
- [ ] **Step 3: Implement the libs, UI primitives, and the workspace layout.** Each route gets a placeholder page for now.
- [ ] **Step 4: Run `npm test` and confirm it passes.** Then run `npm run build` and confirm it exits 0 with no type errors. With the backend stopped, visit `/app` and confirm the offline banner shows.
- [ ] **Step 5: Commit** — `feat(frontend): design system, workspace shell, API client with error states`

---

### Task 11: Web GIS + parcel drawer with "Why was this matched?" (Hour 4–5)

**Files:**
- Create: `frontend/src/components/map/{GisMap.tsx,layers.ts,LayerControl.tsx,MapSearch.tsx,Legend.tsx}`, `frontend/src/components/parcel/{ParcelDrawer.tsx,WhyMatched.tsx,ConfidenceBars.tsx,Provenance.tsx}`, `frontend/src/app/app/map/page.tsx`

**Interfaces:**
- Consumes: `/layers/*`, `/parcels`, `/parcels/{id}`, `statusColor`.
- `GisMap` props: `{ layers: LayerKey[]; selectedParcel?: string; onSelect(parcelId: string): void; focusBbox?: [number,number,number,number]; compact?: boolean }`. It is loaded with `dynamic(() => import(...), { ssr: false })`.
- Map style: an inline style object with a `background` layer `#0b0f14` and no remote sources. Glyphs are not required, and labels are omitted. Layers in draw order:
  - roads: line `#1f2a33`, 6 px
  - parcels-fill: fill with `match-expression` on `match_status`, using the status colours at 0.35 opacity
  - parcels-line: 0.6 px
  - buildings: fill `#94a3b8` at 0.25
  - municipal: dashed teal outline, off by default
  - revenue points and gnss points: circles, off by default
  - topology: red hatch/outline
  - changes: NEW green / MODIFIED amber / REMOVED red outline, off by default
  - selected: accent 2.5 px line
- Toolbar: Layers, Search, a Confidence toggle (colour by status vs grey), Conflicts only (a filter `match_status in [REVIEW, CONFLICT]`), Changes (toggles the changes layer), and Fit to data.
- URL state: `/app/map?parcel=P1023` opens the drawer and flies to the parcel. Flying only happens on selection; there is no continuous animation.
- `ParcelDrawer` layout (right side, full-screen sheet on mobile):
  - header: parcel ID + status pill
  - Owner, Area, Land use
  - Sources checklist: ✓/✗ for Cadastral, Revenue, Municipal, GNSS (count), Buildings (count)
  - Match confidence (large %)
  - Topology status
  - Conflicts (count, links to `/app/conflicts?id=`)
  - `WhyMatched` renders each match's explanation lines, with ✓ green / ! amber / · muted, and `ConfidenceBars` shows the six components with weights and "n/a" for null
  - `Provenance` lists "Cadastral / record P1023", "Revenue / Khasra KH-…", "Municipal / property M…", "GNSS / survey …"
  - `resolved_values` rendered with a "Reviewer-resolved" tag, separate from source values
  - footer: the disclaimer

- [ ] **Step 1: Build the map page** with loading (Skeleton over the map), empty (no run → EmptyState "No harmonized data yet" + "Run harmonization" button linking to `/app/harmonize`), and error (ErrorState + Retry) states.
- [ ] **Step 2: Verify it in a browser** (Playwright MCP or manual) against a seeded, harmonized backend:
  - The map renders 1000 coloured parcels.
  - Clicking a green parcel opens the drawer with ≥ 4 ✓ lines and a "Reason:" line.
  - Searching `P1023` flies to and selects it.
  - The Conflicts-only toggle hides green parcels.
  - Changes shows NEW/MODIFIED/REMOVED outlines.
  - The browser console shows no errors.
- [ ] **Step 3: Commit** — `feat(frontend): Web GIS with confidence styling, layers, search, explainable parcel drawer`

---

### Task 12: Data Sources + Harmonization Workspace (Hour 5–6)

**Files:**
- Create: `frontend/src/app/app/sources/page.tsx`, `frontend/src/components/dashboard/{DatasetTable.tsx,UploadDialog.tsx,Pipeline.tsx,AttributeMappingTable.tsx}`, `frontend/src/app/app/harmonize/page.tsx`
- Modify: `backend/app/api/harmonize.py` to add `GET /harmonization/{run_id}/mappings -> list[{dataset, source_field, canonical_field, confidence, method}]`, with a test added to `test_pipeline.py` asserting that `Owner_Name → owner_name` is present with confidence ≥ 0.9.

**Interfaces:**
- Sources page: a table with the columns Source, Type, Records, CRS (source → `EPSG:32643` after processing), Status pill (registered / ingested / processed / error), Last processed. Raster-type rows (Drone/ORI, DSM/DTM, Utilities) show the badge "Registered — metadata & footprint only". The "Upload dataset" dialog has a file input (accepting `.geojson,.json,.csv,.zip`), a source-type select, and an optional CRS text field. On success it shows a toast; a 422 shows the backend message inline.
- Harmonize page: a "Run harmonization" button → `POST /harmonize` → `pollRun`. The vertical `Pipeline` shows the 7 PRD stages (INGEST … HARMONIZE); each shows pending/running (pulsing accent dot)/done (✓ + duration)/failed and the backend's `detail` string verbatim. Nothing is simulated: the displayed state is only what the run row says. On completion it shows a summary strip (CRS normalized list, matched, conflicts, avg confidence) plus the `AttributeMappingTable` (source field → canonical field with a confidence bar and method) and CTAs "Open map" and "Review conflicts". A 409 shows the toast "A run is already in progress" and attaches to the latest run.

- [ ] **Step 1: Write the backend mappings test, run it and confirm it fails, implement the endpoint, then run it and confirm it passes.**
- [ ] **Step 2: Build both pages** with loading, empty and error states.
- [ ] **Step 3: Verify in the browser:**
  - Upload `data/demo/buildings.geojson` → a new row appears.
  - Uploading a `.txt` shows "Unsupported file type".
  - Run harmonization → the stages progress in order and finish with real numbers matching `/analytics`.
- [ ] **Step 4: Commit** — `feat(frontend): data sources with upload, live truthful pipeline, attribute mappings`

---

### Task 13: Conflict Center (Hour 5–6)

**Files:**
- Create: `frontend/src/app/app/conflicts/page.tsx`, `frontend/src/components/conflicts/{ConflictTable.tsx,ConflictDetail.tsx,SourceCompare.tsx,ResolveBar.tsx}`

**Interfaces:**
- Layout: split view, with the table on the left (60%) and a compact `GisMap` on the right, focused on the selected conflict's bbox. It stacks vertically below 1024 px.
- Filter chips: All · Area · Boundary · Attribute · Duplicate · Topology (the `type` alias param), plus a status select (default Pending Review).
- Table columns: Parcel ID, Type, Source A → Source B, Observed (e.g. "420 m² vs 468 m² (+11.4%)"), Confidence, Status.
- Selecting a row sets `?id=` and opens `ConflictDetail`:
  - "WHY WAS THIS FLAGGED?" with the explanation and "Recommendation: …"
  - `SourceCompare`, a side-by-side table of the canonical fields for cadastral / municipal / revenue with differing cells highlighted amber
  - `ResolveBar` with the buttons "Use cadastral", "Use municipal", "Use revenue" (for value conflicts; each posts Resolved + chosen_source + field), "Accept as-is" (Accepted), and "Ignore" (Ignored), plus an optional note
- After a resolution: a toast "Parcel P… updated — reviewer-resolved value recorded; source records unchanged". The row status updates, and the "Open parcel" link goes to `/app/map?parcel=…`, where the drawer shows the resolved value and the status turns green when no pending conflicts remain.

- [ ] **Step 1: Build the page** with an empty state ("No conflicts match this filter").
- [ ] **Step 2: Verify in the browser:**
  - Filter Area → pick a row → the compare table highlights the area cells.
  - Click "Use cadastral" → the status becomes Resolved.
  - Open the parcel → the drawer shows "Reviewer-resolved" area.
  - If that was the parcel's last pending conflict, it now renders green.
- [ ] **Step 3: Commit** — `feat(frontend): conflict center with side-by-side sources and resolution`

---

### Task 14: Command Center + Analytics (Hour 6–7)

**Files:**
- Create: `frontend/src/app/app/page.tsx`, `frontend/src/app/app/analytics/page.tsx`, `frontend/src/components/dashboard/{KpiRow.tsx,RunTimeline.tsx,RecentConflicts.tsx,DatasetHealth.tsx,Charts.tsx}`

**Interfaces:**
- Consumes: `/analytics`, `/datasets`, `/conflicts?limit=6`, `/harmonization/latest`.
- Command Center (must communicate the product in < 30 s):
  - A 1-line product statement at the top: "Different departments, one trusted parcel view."
  - KPI row: Parcels · Matched · High confidence · Conflicts pending · Topology issues · Avg confidence · Datasets · Last run.
  - `RunTimeline`: the 7 stages with durations from the latest run.
  - `RecentConflicts` (6 rows, each linking to the conflict).
  - `DatasetHealth` (per-dataset records, CRS, status).
  - A compact map preview (`GisMap compact`) linking to `/app/map`.
  - With no run: a single hero EmptyState with a "Run first harmonization" CTA.
- Analytics (Recharts; follow the `dataviz` skill for colours and axes):
  - match distribution bar (HIGH/REVIEW/CONFLICT/UNMATCHED in status colours)
  - confidence histogram
  - conflict breakdown horizontal bar
  - topology stats
  - "Before vs after" data-quality table from `quality_before_after`
  - "Evaluation on synthetic ground truth" card (match precision/recall, area-conflict recall, owner false-positive rate)
  - processing summary (run duration, CRS transforms)

- [ ] **Step 1: Load the `dataviz` skill, then build both pages** with loading, empty and error states.
- [ ] **Step 2: Verify in the browser:** the KPI numbers equal `/analytics` values. The charts render at 375 px width without horizontal page scroll.
- [ ] **Step 3: Commit** — `feat(frontend): command center and analytics`

---

### Task 15: Landing page + cinematic hero asset (Hour 7–8)

**Files:**
- Create: `frontend/src/app/page.tsx` (replacing the default), `frontend/src/components/landing/{Hero.tsx,Pillars.tsx,HowItWorks.tsx}`, `frontend/public/hero/hero.jpg` (+ optional `hero.webm`)

**Interfaces:**
- Hero copy, exactly: eyebrow "BHOOMISYNC AI", H1 "One trusted spatial view of every urban parcel.", sub "AI-powered multi-source land data harmonization.", CTA "Launch Workspace" → `/app`.
- Pillars: Integrate · Harmonize · Validate · Resolve, each with one line.
- "How it works": DIRTY MULTI-SOURCE DATA → BHOOMISYNC AI → HARMONIZED DATA, shown with real counts from `/analytics` when available; static text otherwise.
- The footer states the scope: "Decision-support prototype on synthetic data for SIH26013."
- Hero asset:
  - Higgsfield is not connected in this Claude Code session, so generate the PRD §9 Asset 1 prompt in Higgsfield (web or MCP), export a JPG ≤ 400 KB (1920 px) and, optionally, a WebM ≤ 3 MB (ffmpeg `-crf 34 -an`), and drop them in `public/hero/`.
  - Until then, `Hero.tsx` renders a fallback: an animated SVG of parcel outlines drawn from a static 60-parcel snapshot of `/layers/parcels`, saved at build time to `public/hero/parcels.json`, over a dark radial gradient with a teal accent. It must look finished without the asset.
  - The video is `preload="none"`, poster = the jpg, and it respects `prefers-reduced-motion`. Motion is Framer Motion fade/rise on the hero text only.
- Spend ≤ 45 min.

- [ ] **Step 1: Build the landing page** with the fallback hero; the asset is swapped in when available.
- [ ] **Step 2: Verify:** Lighthouse performance ≥ 80 on `/` (`npx lighthouse http://localhost:3000 --only-categories=performance --quiet`). No layout shift from the hero at 375 px or 1440 px.
- [ ] **Step 3: Commit** — `feat(frontend): cinematic landing page with hero fallback`

---

### Task 16: E2E demo test, polish, README, final verification (Hour 8–12)

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/e2e/demo.spec.ts`, `README.md`, `docs/demo-script.md`

**Interfaces:**
- Consumes: everything above. The Playwright `webServer` starts `npm run dev`. The backend must already be running against a freshly seeded DB (`uv run python -m app.seed`).

- [ ] **Step 1: Write the e2e demo test** (PRD §17, steps 1–15)

```ts
test("full SIH demo loop", async ({ page }) => {
  await page.goto("/"); await page.getByRole("link", { name: "Launch Workspace" }).click();
  await page.getByRole("link", { name: "Data Sources" }).click();
  await expect(page.getByText("EPSG:32643").first()).toBeVisible();
  await page.getByRole("link", { name: "Harmonize" }).click();
  await page.getByRole("button", { name: "Run harmonization" }).click();
  await expect(page.getByTestId("stage-harmonize")).toHaveAttribute("data-status", "done", { timeout: 60_000 });
  await page.goto("/app/map?parcel=P1023");
  await expect(page.getByText("WHY WAS THIS MATCHED?")).toBeVisible();
  await expect(page.getByText("Reason:").first()).toBeVisible();
  await page.goto("/app/conflicts?type=area");
  await page.getByRole("row").nth(1).click();
  await expect(page.getByText("WHY WAS THIS FLAGGED?")).toBeVisible();
  await page.getByRole("button", { name: "Use cadastral" }).click();
  await expect(page.getByText("source records unchanged")).toBeVisible();
  await page.getByRole("link", { name: "Analytics" }).click();
  await expect(page.getByText("Before vs after")).toBeVisible();
});

test("backend offline shows banner, not blank", async ({ page }) => {      // Review Focus 5
  await page.route("**/localhost:8000/**", r => r.abort());
  await page.goto("/app/map");
  await expect(page.getByText("Backend offline")).toBeVisible();
});

test("mobile layout has no horizontal scroll", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  for (const p of ["/", "/app", "/app/map", "/app/conflicts", "/app/analytics"]) {
    await page.goto(p);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= 375)).toBe(true);
  }
});
```
Add `data-testid="stage-<key>"` and `data-status` to the `Pipeline` rows (Task 12).

- [ ] **Step 2: Run the e2e tests.** `npx playwright test`. Expected: 3 passed. Fix only the failures that break the demo loop.
- [ ] **Step 3: Performance pass:**
  - `/layers/parcels` < 1.5 MB and responds in < 500 ms (`curl -w '%{time_total}'`).
  - No React re-render of `GisMap` when the drawer opens: the drawer state lives outside the map component, and the map only updates the `selected` filter via `setFilter`.
- [ ] **Step 4: README.md** with prerequisites (Docker, uv, Node ≥ 20), then:

```
docker compose up -d
cd backend && cp .env.example .env && uv sync && uv run python -m app.seed && uv run uvicorn app.main:app --port 8000
cd frontend && npm i && npm run dev   →  http://localhost:3000
```
plus how to run the tests (`uv run pytest`, `npm test`, `npx playwright test`) and the architecture diagram from PRD §5. Add `docs/demo-script.md` with the 15-step script using the **real** numbers recorded in Task 8 Step 4.
- [ ] **Step 5: Final verification** (REQUIRED SUB-SKILL: superpowers:verification-before-completion):
  - Restart everything from clean (`docker compose down -v && docker compose up -d`, then re-seed).
  - Run all three test suites.
  - Walk the demo manually in under 5 minutes.
  - Check the browser console and backend logs for errors.
  - Check each route at 375 / 768 / 1440 px.
  - Disconnect the network and repeat the map and conflict steps.
- [ ] **Step 6: Commit** — `docs: README, demo script; test: e2e demo loop`
- [ ] **Step 7: Final report** to the user under the PRD §28 headings (IMPLEMENTED / PARTIALLY IMPLEMENTED / NOT IMPLEMENTED / CORE DEMO STATUS / KNOWN ISSUES / HOW TO RUN / DEMO FLOW / NEXT PRIORITIES), citing the test output.

---

### Task 17 (optional, only if Tasks 1–16 are green with ≥ 1 h left): ML match classifier

**Files:**
- Create: `backend/app/engine/ml.py`, `backend/tests/test_ml.py`
- Modify: `backend/pyproject.toml` (add `scikit-learn`), `backend/app/pipeline.py`, `backend/app/api/analytics.py`

**Interfaces:**
- `train_classifier(pairs: list[ScoreBreakdown], labels: list[int]) -> LogisticRegression` is trained on candidate pairs from a **second** synthetic ward (`generate_ward(seed=7)`) labelled via its ground truth. Missing components are imputed as 0.5, with an `is_missing` flag per component.
- `ml_probability(model, b: ScoreBreakdown) -> float` is stored in `evidence["ml_probability"]`. The weighted baseline stays the source of `final_confidence`. Analytics adds `evaluation.ml_match_precision` for comparison, and the drawer shows "ML agreement: 0.97".

- [ ] **Step 1: Failing test:** a model trained on seed 7 reaches ≥ 0.97 precision on the seed-42 ground truth, and `ml_probability` is in [0,1].
- [ ] **Step 2: Implement, run the tests and confirm they pass, then commit** — `feat: optional logistic-regression match classifier (advisory)`

---

## Spec Coverage Map

| PRD requirement | Task |
|---|---|
| A Ingestion (GeoJSON, CSV, ZIP; raster types registered) | 2, 3 |
| B CRS detection/normalization + displayed transform | 3, 8, 12 |
| C Spatial matching + classes + explanation | 5, 8, 11 |
| D Attribute mapping with confidence | 4, 12 |
| E Conflicts with statuses | 6, 9, 13 |
| F Topology + review-gated fixes | 6, 8, 11 |
| G Configurable weighted confidence, component scores | 1 (config), 5, 11 |
| H Web GIS (layers, search, zoom-to-conflict, colours) | 11, 13 |
| I Dashboard + timeline | 14 |
| J Parcel detail + "Why matched?" | 9, 11 |
| §10 seven screens | 11–15 |
| §12 API surface | 1, 3, 8, 9 |
| §13–15 data model + provenance | 3, 8, 9 |
| §16 Change detection | 7, 9, 11 |
| §7 Synthetic data + ground truth + evaluation | 2, 9, 14 |
| §9 Higgsfield hero | 15 |
| §17 Demo flow / §18 verification / §19 DoD | 16 |
| Optional ML | 17 |
