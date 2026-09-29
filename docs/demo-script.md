# UrbanSync AI — 4½-minute demo script

Before you start, reset to a clean state with `uv run python -m app.seed` (backend on :8000, frontend on :3000). All numbers below are deterministic (seed-42 ward) and reproduce exactly on a fresh run. Nothing shown is hard-coded — every figure is served by the backend.

| # | Screen | Do | Say / point at |
|---|---|---|---|
| 1 | Landing `/` | — | "This is **UrbanSync AI** — intelligent spatial data harmonization for India's cities." The hero is India's real geography with the city network; Pune carries the demo chip. |
| 2 | Landing | Scroll to **What are we actually solving?** | Seven kinds of sources, different systems/schemas/geometries → manual reconciliation. UrbanSync turns that into matched features, detected conflicts, explainable confidence. |
| 3 | Landing | Scroll past **How it works** | Six steps: Connect → Normalize → Match → Validate → Explain → Harmonize. |
| 4 | Landing | **Explore India Map** | The India map is the front door: ● Pune demo, ◐ Surat validation, ○ six planned cities. "Designed for India, city by city." |
| 5 | India Map | Search **Mumbai**, click it | Honest empty state: "Dataset not connected yet." — no fake statistics, plus the architecture link. "More city datasets are needed to expand UrbanSync AI across India." |
| 6 | India Map | Click **Pune** | Smooth zoom; the tested urban area is highlighted, and the card shows the honest pre-run state: **1,000 test parcels**, match stats pending — "Run harmonization to see match statistics". (After step 8, revisiting Pune draws all 1,000 harmonized parcels inside the highlight.) |
| 7 | India Map | Click **Explore harmonized parcels** | Lands in the Web GIS with the breadcrumb India / Pune / Demo ward. |
| 8 | Harmonize | Sidebar → **Harmonize** → **Run harmonization** | 7 real backend stages in ~2.5 s: **985 municipal + 1,000 revenue matches**, 15 duplicates, 17/26 fields mapped, 10 gaps · 12 overlaps · 8 self-intersections, **281 conflicts**, plus the ML cross-check agreeing on 98.2%. |
| 9 | Web GIS | Search **P1023** | Drawer: 93% confidence, Cadastral ✓ Revenue ✓ Municipal ✓, Buildings (2). |
| 10 | Web GIS | Read **Why was this matched?** | "82% boundary overlap · 1.4 m centroid distance · 0.1% area difference · 100% owner-name similarity → 89% HIGH-CONFIDENCE MATCH", the Reason line and weighted component bars. |
| 11 | Conflicts | **Conflicts → Area** | 114 area mismatches sorted by detector certainty. |
| 12 | Conflicts | Click the first row (**P1830**) | **Why was this flagged?** "Area differs by 13.0% (423 m² cadastral vs 486 m² municipal)". Side-by-side mapped areas 423 / 486 / 423 m², highlighted; the mini-map zooms to the parcel. |
| 13 | Conflicts | Note "GNSS confirms" → **Use cadastral** | Toast: "reviewer-resolved value recorded; **source records unchanged**." |
| 14 | Web GIS | **Open parcel** | Status turns green labelled ***Reviewer-confirmed*** — the municipal match score honestly stays at 81%; the resolved area carries the Reviewer-resolved tag, note and timestamp, above full provenance. Re-running keeps the decision ("1 reviewer decisions carried forward"). |
| 15 | Analytics | Open **Analytics** | Before vs after: CRS 2 → 1, owner schemas 3 → 1, links 0 → 985, discrepancies surfaced 0 → 281. Evaluation on the synthetic answer key: 100% precision/recall (say clearly: synthetic; real data will score lower). |
| 16 | India Map | Back → click **Surat** | The closer: "The **unchanged engine** re-ran on a second synthetic city — 100% precision and recall against its own answer key. The intelligence layer is city-agnostic; datasets vary by city." |

**Close:** "One spatial view, many urban data sources. It never overwrites a department's record, it explains every link, and every disagreement goes to a human. Plug in the next city's datasets and the same engine does the rest."
