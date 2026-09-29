# UrbanSync Copilot Instructions

## Project Purpose
UrbanSync is the SIH26013 one-day MVP for harmonizing multi-source urban geospatial land records. It is a local-first decision-support demo using controlled synthetic data, not a land-ownership authority. Never present synthetic data or metrics as official government data, and never describe confidence as legal certainty.

Priorities: a working end-to-end demo, geospatial correctness, explainable matching, interactive GIS, conflict review, then visual polish. Keep the current architecture. Do not add microservices, cloud services, queues, or production-scale features for the MVP. Higgsfield assets are optional and must not block local functionality.

## Architecture
- `frontend/`: Next.js App Router, TypeScript, React, Tailwind, MapLibre GL, Recharts, and Framer Motion. The frontend calls the backend REST API; it does not query the database.
- `backend/app/api/`: FastAPI route handlers. `backend/app/pipeline.py` orchestrates the harmonization run and persists truthful stage progress.
- `backend/app/engine/`: geospatial matching, attribute mapping, conflict detection, topology validation, change detection, and advisory ML. Keep domain algorithms testable and independent where possible.
- `backend/app/ingest/`: readers, CRS normalization, and source-feature persistence.
- `backend/app/models.py` and `backend/app/db.py`: SQLAlchemy/PostGIS schema and initialization. `init_db()` creates the PostGIS extension and ORM tables; `docker/init.sql` creates the test database.
- `data/demo/`: deterministic generated inputs and ground truth. `data/validation/`: cached second-city synthetic validation. `data/uploads/`: local uploads.
- `docker-compose.yml`: one PostgreSQL 16 / PostGIS 3.4 service. Do not introduce another service for MVP work.

## Important Directories
- Backend implementation: `backend/app/`; routes: `backend/app/api/`; algorithms: `backend/app/engine/`; ingestion: `backend/app/ingest/`; tests: `backend/tests/`.
- Frontend routes: `frontend/src/app/`; reusable UI: `frontend/src/components/`; API/types/utilities: `frontend/src/lib/`; vendored map data and worker: `frontend/public/`.
- Product requirements and demo flow: `docs/prd.md`, `docs/prd-v2.md`, and `docs/demo-script.md`.
- `.agents/skills/` and `.claude/skills/` contain optional Higgsfield skill material, not app code or required runtime services.

## Local Development
Requirements: Python `>=3.12,<3.13`, Node `>=20`, Docker, `uv`, and npm. At audit time this machine had CPython 3.12.14, FastAPI 0.141.1, Node 24.18.0, npm 11.16.0, and uv 0.12.19. Backend dependencies are locked in `backend/uv.lock`; frontend dependencies are locked in `frontend/package-lock.json`. Use `uv` and npm rather than installing Python packages globally or using a different JS package manager.

Start PostGIS from the repository root:

```sh
docker compose up -d --wait
```

Database defaults are in `backend/app/config.py` and match `backend/.env.example`: `bhoomi:bhoomi@localhost:5433/bhoomisync`; tests use `bhoomisync_test`. Copy `backend/.env.example` to `backend/.env` only when local overrides are needed. Frontend API defaults to `http://localhost:8000`; override with `NEXT_PUBLIC_API_URL` in `frontend/.env.local` only when needed.

Start the backend:

```sh
cd backend
uv sync
uv run python -m app.seed
uv run uvicorn app.main:app --port 8000
```

Start the frontend in another terminal:

```sh
cd frontend
npm ci
npm run dev
```

The frontend is at `http://localhost:3000`; FastAPI is at `http://localhost:8000` and exposes `/health` and interactive API docs at `/docs`.

`uv run python -m app.synthetic` regenerates the deterministic seed-42 demo files in `data/demo/`. `uv run python -m app.seed` generates them if missing, then truncates and reloads source and derived database tables, clearing prior runs and reviewer decisions. Do not reseed casually when preserving a demo review is important.

On the audited macOS machine, Docker Desktop's CLI/helper links were not on the default `PATH`; its bundled binaries worked after adding `/Applications/Docker.app/Contents/Resources/bin` to `PATH`. Keep this machine-specific workaround out of project scripts.

## Tests and Checks

```sh
cd backend && uv run pytest -q
cd frontend && npm test
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npx playwright test
```

Backend tests use PostGIS and the `TEST_DATABASE_URL` database. Playwright's demo flow needs the backend, frontend, and seeded database. The Playwright config starts/reuses the frontend; it does not start the backend or seed data.

## Geospatial and Data Rules
- Project/storage CRS is `EPSG:32643` (UTM zone 43N, metres). Normalize source geometry at ingestion; geometry columns use SRID 32643.
- GeoJSON served to the browser is transformed to `EPSG:4326` with longitude/latitude coordinate order. Keep API geometry payloads in GeoJSON FeatureCollection form.
- Use the existing GeoPandas, Shapely, PyProj, GeoAlchemy, and PostGIS utilities. Do not invent CRS math or replace spatial operations with string/coordinate hacks.
- Source features are immutable. Reviewer choices and safe corrections belong on canonical/derived records; never silently rewrite source data.
- Preserve provenance from canonical parcels to source datasets/features. Keep confidence scores and conflict recommendations explainable and evidence-based.
- Synthetic generator defaults to seed 42; the advisory logistic-regression check trains on a separate synthetic seed and does not replace the weighted confidence score.
- Raster/imagery/DSM/DTM/utility sources are metadata-only in this MVP. Do not imply raster processing exists.

## Backend Conventions
- Add routes to the existing `backend/app/api/` modules and register them in `backend/app/main.py`; API paths currently have no `/api` prefix.
- Reuse SQLAlchemy models, Pydantic schemas, `get_session`, ingestion readers, and common response helpers. There is no Alembic migration workflow; schema setup uses `init_db()`/`Base.metadata.create_all()`.
- The pipeline stages are Ingest, Normalize CRS, Spatial match, Map attributes, Validate topology, Detect conflicts, and Harmonize. Keep run state and result metrics backed by database records, not fabricated UI values.
- Make focused engine changes alongside the existing tests in `backend/tests/`. Use the current API and ORM contracts unless the requested behavior requires changing them.

## Frontend Conventions
- Use the existing App Router routes: `/`, `/app`, `/app/india`, `/app/sources`, `/app/harmonize`, `/app/map`, `/app/conflicts`, and `/app/analytics`.
- Reuse existing components under `frontend/src/components/`, API helpers in `frontend/src/lib/api.ts`, and shared API types in `frontend/src/lib/types.ts`. Keep displayed KPIs and status values sourced from the backend.
- MapLibre components are client-only and dynamically imported with SSR disabled. Keep the vendored worker URL and local GeoJSON assets; the maps intentionally use no external tile server.
- Preserve the current PRD-v2 light visual system and map-first operational hierarchy. Avoid a generic marketing-dashboard redesign or animation that interferes with map interaction.
- Provide loading, empty, and error states for API-backed views. Keep selection, conflict focus, and resolution connected to actual API state.

## Existing API Surface
- `GET /health`
- `GET /datasets`, `POST /datasets/upload`
- `POST /harmonize`, `GET /harmonization/latest`, `GET /harmonization/{run_id}`, `GET /harmonization/{run_id}/mappings`
- `GET /parcels`, `GET /parcels/{parcel_id}`
- `GET /conflicts`, `GET /conflicts/{conflict_id}`, `POST /conflicts/{conflict_id}/resolve`
- `GET /layers/{layer}` for parcels, topology, conflicts, municipal, revenue, buildings, GNSS, roads, and changes
- `GET /analytics`, `GET /cities`, `GET /cities/{city_id}`

## MVP Status and Known Caveats
The repository already implements deterministic synthetic inputs, ingestion, CRS normalization, weighted matching and explanations, attribute mapping, topology/conflict detection, reviewer resolution, analytics, a MapLibre parcel map, India city map, parcel drawer, and a Playwright demo workflow. Extend these features rather than duplicating them. Real government connectors, raster processing, authentication/RBAC, and production nationwide operation are out of scope.

The root contains an empty `package-lock.json` as well as the real `frontend/package-lock.json`, but no root `package.json`. Next.js/Turbopack may warn about workspace-root inference and multiple lockfiles; this is non-blocking. A previous lint run reported warnings but no errors; do not spend MVP time on unrelated vendor/generated-file warnings. A previous backend test warning came from Starlette's `httpx` TestClient deprecation.

Audit snapshot (2026-09-29): Docker reported the database healthy on port 5433 with PostGIS 3.4.3 and 10 seeded datasets. There were zero harmonization runs and zero canonical parcels, as expected after seeding until `/harmonize` is run. Requests to ports 3000 and 8000 did not connect during the audit; check current processes before assuming either server is running. The backend `.env` and frontend `.env.local` were absent; defaults are configured in code.

## MCP Independence
Do not assume MCP servers or remote AI tools exist. No MCP server configuration or runtime dependency was found in this repository. Higgsfield references in `.agents/`, `.claude/`, and `skills-lock.json` are optional asset-generation workflows only. Keep app development, tests, data generation, and demo operation fully local; never block work on MCP or Higgsfield availability.

## Git Safety
The user controls Git and GitHub attribution. Do not commit, push, amend, rebase, reset, force-update, create branches, or otherwise modify Git history unless explicitly requested. Do not discard or overwrite user changes. Do not assume `.git` metadata exists in ZIP-extracted copies.
