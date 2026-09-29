# UrbanSync AI — Redesign PRD (v2)

> Condensed with full fidelity from the redesign brief supplied on 2026-09-28. Evolves the existing BhoomiSync MVP (docs/prd.md); does not replace working functionality. This is the spec the v2 implementation plan argues from.

## 1. Rename
BhoomiSync AI → **UrbanSync AI**, everywhere visible: browser title, logo/wordmark, nav, landing, dashboard, metadata, empty states, about/help, docs, README. No visible "BhoomiSync" remains.
- Primary tagline: **"Intelligent spatial data harmonization for India's cities."**
- Secondary: **"UrbanSync AI brings fragmented urban land and geospatial datasets together into one trusted, explainable spatial view."**

## 2–3. Product story
Not "another GIS dashboard". Message: India has many urban datasets describing the same physical places (cadastral, revenue, municipal GIS, drone, ORI, GNSS/CORS, GT, footprints, utilities, DSM/DTM) with different CRSs, boundaries, identifiers, schemas, accuracy, dates. UrbanSync AI is the intelligent harmonization layer. The workflow must be visually obvious: SOURCES → NORMALIZATION → SPATIAL MATCHING → ATTRIBUTE HARMONIZATION → CONFLICT DETECTION → TOPOLOGY VALIDATION → CONFIDENCE SCORING → HUMAN REVIEW → HARMONIZED URBAN MAP.

## 4–7. India-first geography (core UX)
Open on an **India-wide map**, not the tiny local ward. Drill-down: INDIA → STATE → CITY → URBAN AREA/WARD → TESTED AREA → PARCEL. India map: outline + state boundaries, major/test cities, data-availability indicators, clean light basemap, restrained labels. Tested/synthetic area highlighted on the India map. Click city → smooth zoom → show tested area boundary → CTA **"Explore harmonized parcels"** into the parcel Web GIS.
Demo city: "Use whichever city is easiest for the current synthetic dataset. If an existing test dataset already corresponds to a city, use that city." (Existing ward is Pune.) Label clearly: **Demo / Synthetic Dataset**. Never imply official government data.

## 6, 8–9, 30–33, 36. Multi-city architecture
Extensible `CityProfile { id, name, state, coordinates, status, datasetStatus, datasetType, testArea, parcelCount, matchedCount, conflictCount, confidence }` for: ahmedabad, delhi, mumbai, bengaluru, hyderabad, pune, jaipur, surat. One fully tested demo city; others "○ Dataset integration planned". Sections: **"Expanding Across India's Cities"** (status list, "More city datasets coming"), **"Built for more cities, not just one test area."** (CITY DATASET → SOURCE CONNECTORS → NORMALIZATION → URBANSYNC AI ENGINE → CITY HARMONIZED LAYER), **"Designed to generalize across cities"** (same engine, varying sources). City search: unavailable → "Dataset not connected yet." + "Request / add city dataset" + [View architecture]; never fake statistics. Don't hardcode the demo area everywhere; city pipeline: CITY DATA → INGESTION → NORMALIZATION → MATCHING → VALIDATION → HARMONIZATION → CITY MAP.

## 10–12. Explain the problem; never overclaim
Prominent landing section **"What are we actually solving?"**: Problem (7 sources → different systems/schemas/geometries/identifiers → manual reconciliation) vs UrbanSync AI (sources → spatial+attribute intelligence → matched features → detected conflicts → explainable confidence → harmonized view). Result line: **"Instead of manually comparing thousands of records, urban data teams can focus their attention on the records that actually need review."**
**"Where UrbanSync AI can help"** — 6 use-case cards (described as use cases, not deployments): 01 Cadastral Harmonization, 02 Revenue + Municipal Reconciliation (schema mapping), 03 GNSS/Ground Truth Validation, 04 Building Footprint Verification, 05 Urban Change Detection (2025 no footprint → 2026 new building), 06 Utility/Parcel Alignment.
Distinguish Current MVP (synthetic demo data; matching, confidence, conflicts, attribute mapping, Web GIS) from Future/planned (real municipal/revenue data, gov APIs, drone/ORI/DSM/DTM, GNSS/CORS, utilities, multi-city production). Use "Designed to integrate" / "Demonstrated with controlled test data."

## 13–16. Premium LIGHT UI
Replace dark SaaS theme. Feel: premium urban intelligence / high-end geospatial analytics / professional government technology. Warm off-white background, white/slightly translucent panels, very subtle gray borders, deep-charcoal text, ONE accent (deep teal / sophisticated blue-green). Avoid neon, purple, rainbow gradients, oversaturation. Map is the visual hero: pale neutral basemap, clean boundaries, subtle roads/labels, tested area stands out with a subtle translucent accent overlay. Hovering a tested city shows a card (name, "Demo dataset", live parcel/matched/conflict/confidence stats, [Explore area]); click → smooth zoom → test boundary → explore CTA.

## 17–21. Landing structure
HERO: eyebrow "INDIA'S URBAN SPATIAL INTELLIGENCE LAYER"; headline **"One spatial view. Many urban data sources."**; support "UrbanSync AI harmonizes fragmented cadastral, municipal, revenue, survey and geospatial datasets into a unified, explainable urban land view."; CTAs **Explore India Map** / **See How It Works**. Hero visual = India map with city nodes, subtle animated connections, highlighted demo city, small data indicators — NOT a generic stock city image.
"How it works": 01 Connect · 02 Normalize · 03 Match · 04 Validate · 05 Explain · 06 Harmonize (one line each).
**"See the system in action"**: large map, left stats (demo city, test parcels/matched/conflicts/avg confidence — real values), highlighted test area, CTA "Open interactive map" → Web GIS.
Test-data disclosure near it: "**Demo dataset** — The current demonstration uses controlled/synthetic urban data to validate the harmonization workflow. Additional city datasets can be plugged into the same architecture."

## 22–27. Workspace redesign
Same light theme. Sidebar: UrbanSync AI / Overview, India Map, Datasets, Harmonization, Conflicts, Validation, Analytics; bottom "Demo Workspace". Command Center: "India · 8 city profiles · 1 active demo dataset", KPI cards (real numbers), large map. **India Map is the primary navigation destination** (● Demo dataset / ○ Planned). Parcel map keeps parcels, buildings, conflicts, confidence, GNSS, minimal controls (Layers, Confidence, Conflicts, Sources, Search parcel). Parcel detail and conflict comparison keep the existing explainable content in the clean new IA.

## 28. Higgsfield
Only assets that improve the product. Asset 1: "Premium editorial aerial visualization of a dense Indian city integrated with a clean India map interface, subtle cadastral parcel geometry, urban planning grid, sophisticated light background, architectural visualization aesthetic, restrained teal spatial highlights, high-end enterprise geospatial technology, no text, no logos." Asset 2 (optional): short India→city→area→parcels motion. Keep the app fast.

## 29. Responsive
Desktop, laptop, tablet. Map usable. No full mobile GIS today.

## 34. Real India geography
Use actual boundaries from a legitimate source; no hand-drawn India. Vendor the dataset locally; the demo must not depend on a live external service.

## 35–36. Second city validation
Run the same harmonization model on a second controlled dataset (same schema, different city), labelled **"Synthetic validation dataset."** Goal: demonstrate the model is city-agnostic. Never present synthetic data as official.

## 37–38, 42–43. Constraints & priorities
Do not break existing functionality: inspect, run, preserve engine/APIs/data pipeline; refactor only where required; no backend rewrite for aesthetics. Priority order: India map → city drill-down → test-area highlight → existing harmonization workflow → premium light UI → problem/use-case explanation → multi-city architecture → Higgsfield visuals. **Do not stop at static design**: every important visual connects to actual application state (real zoom, real datasets, real confidence/conflicts). No fake metrics.

## 39–41, 44–45. Success criteria & verification
30-second comprehension: WHAT (harmonizes urban geospatial datasets), WHERE (India's cities), PROBLEM (sources disagree about the same land), HOW (matching + mapping + validation + confidence), DEMO (India → city → tested area → parcel → conflict → explanation). Final journey: LANDING → INDIA MAP → SELECT CITY → TESTED AREA → EXPLORE PARCELS → PARCEL → SOURCES → CONFIDENCE → CONFLICT → WHY → RESOLVE → HARMONIZED RESULT. Not a generic gov portal / GIS app / AI SaaS / cyberpunk. Manual verification checklist (44) incl. unavailable-city messaging, backend-generated results, no fake metrics, no external network dependency where possible. Final report format (45) with functional verification per feature, demo dataset details, secondary validation, known limitations, how to run.
