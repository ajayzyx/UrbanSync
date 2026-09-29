# BhoomiSync AI — SIH26013 — One-Day MVP PRD

> Saved verbatim-in-substance from the PRD supplied on 2026-09-28 (encoding artefacts fixed, citation markers removed). This is the spec the implementation plan argues from.

**Version:** 1.0 · **Target build time:** 1 day · **Builder:** Claude Code (+ Higgsfield for visual assets)
**Objective:** A working, demo-ready MVP — not a production nationwide land-record platform.

## 1. Executive Objective

Build a functional MVP for **SIH26013: Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management**.

Workflow: **Upload multi-source land datasets → inspect and normalize → spatially match features → intelligently map attributes → detect conflicts → validate topology → calculate confidence → visualize the harmonized result on an interactive Web GIS dashboard.**

The system is a **decision-support and data-harmonization platform**. It must NOT claim to legally determine land ownership or replace authorized cadastral/revenue decisions.

## 2. Product Name

**BhoomiSync AI** — tagline: **"One trusted spatial view of every urban parcel."** Short descriptor: **"AI-powered urban land data harmonization."**

## 3. Core Problem

Urban land information exists across drone imagery, ORI, DSM/DTM, cadastral maps, revenue records, municipal GIS, utility networks, ground truthing (GT), GNSS/CORS survey data and building footprints. They differ in CRS, geometry, precision, identifiers, attribute names, attribute values, survey dates, completeness and topological correctness. BhoomiSync AI is an interoperability layer that processes these differences and presents a unified, explainable spatial view.

## 4. One-Day MVP Scope — MUST BUILD

**A. Dataset ingestion.** GeoJSON; CSV with latitude/longitude; optional Shapefile/ZIP. Demo categories: cadastral parcels, municipal parcels, revenue records, building footprints, GNSS/GT points. Imagery/DSM/DTM/ORI may be registered source types with metadata and sample footprints — no raster pipeline.

**B. CRS normalization.** CRS detection, common project CRS, transformation via established libraries, validation of transformed geometries. Display e.g. `EPSG:4326 → EPSG:32643`.

**C. Spatial matching engine (primary intelligence feature).** Per candidate pair: centroid distance, area difference, IoU/overlap, boundary overlap, shape similarity, attribute similarity, building overlap, temporal difference. Produce match probability/confidence, match class, explanation. Weighted baseline acceptable; optional ML classifier on synthetic labels. Classes: **HIGH CONFIDENCE, REVIEW, CONFLICT**.

Example:
```
Parcel P1023 ↔ Municipal M7781
Geometry similarity: 91%  Centroid proximity: 96%  Area similarity: 94%  Attribute similarity: 88%
Overall confidence: 93%   Classification: HIGH-CONFIDENCE MATCH
```

**D. Intelligent attribute mapping.** Revenue (`Khasra_No, Owner_Name, Land_Area, Land_Type`) and Municipal (`Property_ID, Owner, Area, Usage`) map to canonical fields:
```
Khasra_No → parcel_id        Property_ID → source_property_id
Owner_Name → owner_name      Owner → owner_name
Land_Area → area             Area → area
Land_Type → land_use         Usage → land_use
```
Display mapping confidence. No enterprise ontology.

**E. Conflict detection.** Area mismatch, owner/attribute mismatch, duplicate feature, boundary overlap, missing attribute, spatial mismatch. Each conflict: Parcel ID, Conflict type, Source A, Source B, Observed values, Confidence, Recommended action, Status. Statuses: **Pending Review, Accepted, Resolved, Ignored**.

**F. Topology validation.** Polygon overlaps, gaps where practical, invalid geometries, self-intersections. Automated correction only where safe and deterministic; otherwise "Correction suggested — requires review." Do not silently alter authoritative land geometry.

**G. Confidence scoring.** Explainable per feature. Example (configurable):
```
30% geometry similarity, 20% centroid proximity, 15% area similarity,
15% shape/boundary similarity, 10% attribute similarity, 10% temporal/source consistency
```
Show component scores. Never present confidence as legal certainty.

**H. Interactive Web GIS.** MapLibre GL JS; parcel polygons, layer controls, feature selection, search, zoom to conflict, confidence styling (High → green, Review → amber, Conflict → red). Avoid effects that hurt readability.

**I. Dashboard.** Datasets processed, parcels processed, matched features, high-confidence matches, conflicts, topology issues, average confidence, last harmonization run; activity/process timeline.

**J. Parcel detail panel.** Owner, area, sources (✓ Cadastral / Revenue / Municipal / GNSS), match confidence, topology, conflicts; "Why was this feature matched?" with evidence.

## 5–6. Architecture & Stack

Next.js + TypeScript + Tailwind + MapLibre (+ Framer Motion sparingly, Recharts) → REST → FastAPI (GeoPandas, Shapely, PyProj, scikit-learn optional) → PostgreSQL/PostGIS. Local first; Docker if time permits. No microservices, Kubernetes, queues or complex cloud.

## 7. Data Strategy

Synthetic urban ward: ~1,000 parcels, ~1,500 buildings, roads, utilities where useful, GNSS/GT points, revenue records, municipal records. Intentional discrepancies: area mismatches, owner-name variations, small coordinate shifts, duplicates, missing attributes, boundary overlaps, invalid geometries. Plus a small ground-truth dataset for evaluation. Story: DIRTY MULTI-SOURCE DATA → BHOOMISYNC AI → HARMONIZED DATA. Never fabricate claims about real government data.

## 8. UI/UX Direction

Cinematic SaaS aesthetic (Prompt 08 — SaaS/App of the One-Prompt Website Pack) adapted for government geospatial intelligence: deep charcoal/near-black shell, off-white type, one restrained geospatial accent (cyan/teal), subtle grid/topographic patterns, glass panels only where readable, thin borders, map-first hierarchy, restrained motion, technical micro-labels, clear status indicators. Avoid purple AI gradients, heavy glassmorphism, fake 3D dashboards, marketing copy in the operational dashboard, animations that slow GIS interaction.

## 9. Higgsfield Usage

Asset 1 (priority) — hero background: "Aerial night-to-dawn view of a dense Indian urban district, subtle cadastral parcel boundaries and geospatial grid overlays emerging over the city, professional government geospatial intelligence aesthetic, dark cinematic lighting, restrained cyan/teal spatial highlights, realistic aerial perspective, no readable text, no logos."
Asset 2 (optional) — layers → alignment → fusion → unified parcel map clip. Skip if costly. Working dashboard matters more.

## 10. Screens (only these)

1. **Landing** — "BHOOMISYNC AI / One trusted spatial view of every urban parcel. / AI-powered multi-source land data harmonization. / [Launch Workspace]"; hero visual; Integrate · Harmonize · Validate · Resolve. ≤45 min.
2. **Command Center** — KPI cards (Parcels, Matched, Conflicts, Avg Confidence), pipeline, recent conflicts, dataset health, map preview.
3. **Data Sources** — Cadastral, Revenue, Municipal GIS, Building Footprints, GNSS/GT, Drone/ORI, DSM/DTM, Utilities; each with Source, Records, CRS, Status, Last processed.
4. **Harmonization Workspace** — INGEST → NORMALIZE → MATCH → MAP ATTRIBUTES → VALIDATE → RESOLVE → HARMONIZE; live-looking but truthful state from real backend operations.
5. **Web GIS** — Layers, Search, Confidence, Conflicts, Changes, Fit to data; click parcel → detail drawer.
6. **Conflict Center** — table + map; filters All/Area/Boundary/Attribute/Duplicate/Topology; row opens parcel.
7. **Validation / Analytics** — match distribution, confidence distribution, conflict breakdown, topology stats, processing summary.

## 11. AI Explanation UX

"WHY WAS THIS MATCHED?" — ✓ 94% boundary overlap, ✓ 1.8m centroid distance, ✓ 0.7% area difference, ✓ 91% attribute similarity; overall confidence; reason sentence.
"WHY WAS THIS FLAGGED?" — e.g. "Area differs by 6.8%. Municipal and revenue geometries overlap by only 72%." Recommendation: "Manual review required."

## 12. API

```
GET /health  GET /datasets  POST /datasets/upload  POST /harmonize  GET /harmonization/{run_id}
GET /parcels  GET /parcels/{id}  GET /conflicts  GET /conflicts/{id}  POST /conflicts/{id}/resolve
GET /analytics  GET /layers/{layer}
```

## 13–15. Data Model & Provenance

Entities: datasets, source_features, canonical_parcels, attribute_mappings, feature_matches, conflicts, topology_issues, harmonization_runs.
feature_matches: source_feature_id, target_feature_id, geometry_score, centroid_score, area_score, attribute_score, final_confidence, match_class, explanation.
Canonical parcel: id, parcel_id, geometry, area, owner_name, land_use, source_count, confidence_score, match_status, last_updated. Source provenance must never be discarded (e.g. "Cadastral / record 8892, Revenue / Khasra 104, Municipal / property 7781, GNSS / survey 2201").

## 16. Change Detection

Dataset version A vs B: added, removed, significant geometry change, attribute change → NEW / MODIFIED / REMOVED / UNCHANGED. Deterministic spatial comparison is fine.

## 17. Demo Workflow (3–5 min, never dependent on an external API)

Open app → Command Center → Data Sources → upload/select datasets → Run Harmonization → show CRS normalized / N matches / N conflicts / avg confidence → map → click high-confidence parcel → AI explanation → open conflict → source values side-by-side → resolve → harmonized parcel → Analytics → before/after data-quality metrics.

## 18. Execution Plan (hour blocks)

0–1 setup (frontend loads, `/health` 200) · 1–2 synthetic data + DB · 2–4 harmonization engine · 4–5 Web GIS · 5–6 conflicts + validation UX · 6–7 dashboard + analytics · 7–8 cinematic UI · 8–9 explanations + polish · 9–10 testing · 10–11 performance · 11–12 final verification & report.

## 19. Definition of Done

Functional: frontend, backend, database run; synthetic data loads; ingestion; CRS normalization; matching; confidence; attribute mapping; conflicts; topology; ≥1 conflict resolvable; harmonized data on map; parcel details; analytics; provenance visible.
UX: no dead buttons on core workflows; loading/error/empty states; usable map; responsive; consistent type; clear hierarchy.
Demo: offline/local; deterministic data; 3–5 min flow; explainable AI; no unsupported claims.

## 20. Non-Goals

Nationwide DB, legal adjudication, real gov auth, production approval workflow, drone photogrammetry, full DSM/DTM, satellite segmentation, real-time sync, SMS/push, blockchain, Kubernetes, microservices, event streaming, advanced DL, offline mobile app, enterprise RBAC, production cloud deployment.

## 21. Roadmap

Phase 2: real connectors, raster/drone/DSM, CORS/GNSS, better ML, advanced topology repair. Phase 3: imagery change detection, CV building extraction, cadastral extraction, department APIs, multi-city, role-based review. Phase 4: cloud scale, event sync, governance, audit trails, advanced GeoAI.

## 22–26. Operating, Performance & Security Rules

Priority: working MVP > end-to-end demo > correct geospatial behaviour > clear UX > visual polish > advanced features. Loop per feature: PLAN → IMPLEMENT → RUN → TEST → VERIFY → MOVE ON.
Performance: compress video, lazy-load media, no huge background video on every page, reasonable map payloads, simplify geometries, avoid re-renders, never animate the map continuously.
Security: validate upload types, never execute uploads, sanitize metadata, no DB credentials in frontend, keep provenance, never silently overwrite source records, mark AI-recommended changes separately from authoritative data.

## 27–29. Message & Final Report

Judges must grasp in 30 s: different departments have different land datasets; BhoomiSync AI brings them into one spatial reference system, matches features, detects conflicts, validates geometry, assigns explainable confidence, and gives authorized users one harmonized view.
Final report headings: IMPLEMENTED / PARTIALLY IMPLEMENTED / NOT IMPLEMENTED / CORE DEMO STATUS / KNOWN ISSUES / HOW TO RUN / DEMO FLOW / NEXT PRIORITIES. Do not claim completion without running and verifying.
**Golden rule: BUILD THE DEMO, NOT THE DREAM.** UPLOAD → AI HARMONIZATION → MATCH → CONFLICT → EXPLAIN → RESOLVE → TRUSTED MAP.
