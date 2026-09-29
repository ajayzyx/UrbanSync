# UrbanSync AI — SIH26013

**Intelligent spatial data harmonization for India's cities.** UrbanSync AI brings fragmented urban land and geospatial datasets together into one trusted, explainable spatial view.

Different departments keep different land datasets describing the same physical places. UrbanSync AI brings them into one spatial reference system, matches corresponding features, detects conflicts, validates geometry, assigns an explainable confidence score, and gives authorized reviewers a single harmonized view — city by city across India. Every canonical record keeps its provenance. Source records are never modified.

The front door is a real **India map** (vendored state boundaries): Pune carries the demo/synthetic ward, Surat carries a synthetic validation dataset proving the engine is city-agnostic, and six more cities are registered as planned integrations (`GET /cities`). Adding a city = one registry entry + its datasets; the harmonization engine stays unchanged.

> Decision-support prototype on **synthetic** data. It does not determine legal ownership.

## Architecture

```
                    WEB GIS
     Next.js 16 + MapLibre (no external tiles)
                       |
                    REST API
                       |
                    FastAPI
                       |
        +--------------+--------------+
        |              |              |
   Ingestion      Harmonization   Validation
   readers.py     matching.py     topology.py
   normalize.py   attributes.py   conflicts.py
   (PyProj/GPD)   confidence      changes.py
        |              |              |
        +--------- pipeline.py -------+
                       |
          PostgreSQL 16 + PostGIS 3.4 (Docker)
```

- `backend/app/engine/` holds pure functions over GeoDataFrames: attribute mapping, matching and confidence, conflicts, topology, and change detection.
- `backend/app/pipeline.py` runs the 7 stages (Ingest → Normalize CRS → Spatial match → Map attributes → Validate topology → Detect conflicts → Harmonize). It commits each stage as it finishes, so the UI shows real progress.
- All geometry is stored in **EPSG:32643** (UTM 43N) and served to the browser as EPSG:4326.

## Multi-city architecture

```
CITY DATASET → SOURCE CONNECTORS → NORMALIZATION → URBANSYNC AI ENGINE → CITY HARMONIZED LAYER
```

- `backend/app/cities.py` — the city registry (8 profiles: demo / validation / planned).
- `GET /cities` — live stats for the demo city (never invented; nulls before the first run), the highlighted test-area geometry, and the measured validation report for the second city.
- `python -m app.validate` — re-runs the **unchanged** engine on a second synthetic ward (Surat, seed 11) and stores measured precision/recall (also built automatically by the seed).

## Run it

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/), and Node ≥ 20.

```bash
docker compose up -d --wait                            # PostGIS on :5433 (waits until healthy)

cd backend
cp .env.example .env
uv sync
uv run python -m app.seed                              # generates + loads the synthetic ward (deterministic, seed 42)
uv run uvicorn app.main:app --port 8000

cd ../frontend
npm install
npm run dev                                            # http://localhost:3000
```

Everything runs offline once dependencies are installed. The map uses no basemap tiles.

To reset the demo, run `uv run python -m app.seed` again. It reloads the datasets and clears all runs and resolutions.

### Optional hero asset

To use a cinematic render (for example from Higgsfield), put it in `frontend/public/hero/` (≤ 400 KB JPG) and set `NEXT_PUBLIC_HERO_IMAGE=/hero/hero.jpg` in `frontend/.env.local`. Without it, the landing page draws the real ward as an animated vector field.

## Tests

```bash
cd backend && uv run pytest -q          # engine, ingestion, pipeline, API (PostGIS test DB)
cd frontend && npm test                 # unit tests (vitest)
cd frontend && npx playwright test      # e2e demo loop; needs the backend running on a seeded DB
```

## Synthetic data

`python -m app.synthetic` writes `data/demo/`: a 1,000-parcel ward in Pune (25 blocks), in several source schemas and coordinate systems.

| Source | CRS | Schema |
|---|---|---|
| Cadastral parcels | EPSG:32643 | `parcel_id, survey_no, owner_name, area_sqm, land_use, survey_date` |
| Municipal GIS (v1 + v2 update) | EPSG:4326 | `Property_ID, Owner, Area, Usage, Updated_On` |
| Revenue register (CSV points) | lat/lon | `Khasra_No, Owner_Name, Land_Area, Land_Type` |
| Buildings, GNSS/GT, roads | EPSG:4326 | — |
| Drone/ORI, DSM/DTM, utilities | — | registered metadata + footprint only |

The following discrepancies are injected deliberately and recorded in `ground_truth.json`, which the Analytics page uses for evaluation:

- area mismatches
- owner-name variants (which must *not* be flagged) and genuinely different owners
- duplicates
- missing attributes
- large coordinate shifts
- self-intersecting rings, overlaps and gaps
- a v2 municipal update with new, removed and modified records

## Geography

India state boundaries are vendored at `frontend/public/geo/` (no runtime network dependency), simplified from the [DataMeet community maps](https://github.com/datameet/maps) (CC-BY 4.0) via `frontend/scripts/build-india-geo.py`.

## Demo flow

See [docs/demo-script.md](docs/demo-script.md).

## API

`GET /health` · `GET /datasets` · `POST /datasets/upload` · `POST /harmonize` · `GET /harmonization/{id|latest}` · `GET /harmonization/{id}/mappings` · `GET /parcels?q=&status=` · `GET /cities` · `GET /cities/{id}` · `GET /parcels/{id}` · `GET /conflicts?type=&status=` · `GET /conflicts/{id}` · `POST /conflicts/{id}/resolve` · `GET /layers/{parcels|municipal|revenue|buildings|gnss|roads|topology|conflicts|changes}` · `GET /analytics`
