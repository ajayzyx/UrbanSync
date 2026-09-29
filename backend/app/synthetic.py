"""Deterministic synthetic urban ward (Pune, UTM 43N) with injected multi-source discrepancies.

Run: `python -m app.synthetic` -> writes to settings.data_dir.
Every defect is recorded in ground_truth.json so matching / conflict detection can be evaluated.
"""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.affinity import scale, translate
from shapely.geometry import LineString, Polygon, box, mapping

ORIGIN_LONLAT = (73.8567, 18.5204)
BLOCKS_X, BLOCKS_Y = 5, 5
ROWS, COLS = 2, 20
PARCEL_W, PARCEL_H = 15.0, 28.0
ROAD_W = 12.0
BLOCK_W, BLOCK_H = COLS * PARCEL_W, ROWS * PARCEL_H

FIRST = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Suresh", "Kavita", "Rohan", "Meera",
         "Arjun", "Pooja", "Nikhil", "Deepa", "Sanjay", "Neha", "Manoj", "Asha", "Karan", "Swati",
         "Ajay", "Rekha", "Vivek", "Lata", "Prakash", "Shalini", "Ganesh", "Madhuri", "Harish", "Usha",
         "Omkar", "Sunita", "Tushar", "Vaishali", "Yogesh", "Aarti", "Nitin", "Jyoti", "Sachin", "Smita"]
LAST = ["Sharma", "Deshmukh", "Patil", "Kulkarni", "Joshi", "Jadhav", "Pawar", "Shinde", "Gaikwad", "More",
        "Kale", "Bhosale", "Chavan", "Naik", "Iyer", "Reddy", "Gupta", "Verma", "Mehta", "Shah",
        "Rao", "Nair", "Kapoor", "Agarwal", "Bansal", "Sawant", "Salunkhe", "Mane", "Thakur", "Pandey"]
LAND_USES = ["Residential", "Commercial", "Mixed Use", "Institutional", "Open Space"]
LAND_USE_P = [0.62, 0.16, 0.12, 0.06, 0.04]
BASE_DATE = date(2019, 1, 1)


def _round(geom, digits: int):
    return shapely.transform(geom, lambda c: np.round(c, digits))


def _fc(features: list[dict], crs_epsg: int | None = None) -> str:
    fc: dict = {"type": "FeatureCollection"}
    if crs_epsg and crs_epsg != 4326:
        fc["crs"] = {"type": "name", "properties": {"name": f"urn:ogc:def:crs:EPSG::{crs_epsg}"}}
    fc["features"] = features
    return json.dumps(fc, separators=(",", ":"))


def _feature(props: dict, geom, digits: int) -> dict:
    return {"type": "Feature", "properties": props, "geometry": mapping(_round(geom, digits))}


def _name_variant(name: str, rng: np.random.Generator) -> str:
    first, last = name.split(" ")
    kind = int(rng.integers(0, 4))
    if kind == 0:
        return f"{first[0]}. {last}"
    if kind == 1:
        return f"{last.upper()} {first.upper()}"
    if kind == 2:
        return name.lower()
    return f"{first}  {last} "


def _different_name(name: str, rng: np.random.Generator) -> str:
    first, last = name.split(" ")
    while True:
        f, l_ = FIRST[int(rng.integers(len(FIRST)))], LAST[int(rng.integers(len(LAST)))]
        if f != first and l_ != last:
            return f"{f} {l_}"


def _shift(geom, rng: np.random.Generator, lo: float, hi: float):
    d, theta = rng.uniform(lo, hi), rng.uniform(0, 2 * np.pi)
    return translate(geom, d * np.cos(theta), d * np.sin(theta))


def generate_ward(out_dir: Path, seed: int = 42, origin_lonlat: tuple[float, float] = ORIGIN_LONLAT) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    to_utm = Transformer.from_crs(4326, 32643, always_xy=True)
    to_ll = Transformer.from_crs(32643, 4326, always_xy=True)
    ox, oy = (round(v) for v in to_utm.transform(*origin_lonlat))

    def ll(geom):
        return shapely.transform(geom, lambda c: np.column_stack(to_ll.transform(c[:, 0], c[:, 1])))

    # ---- base parcels on a shared, jittered vertex grid (topologically clean) ----
    base: list[Polygon] = []
    meta: list[dict] = []  # block/row/col per parcel
    for by in range(BLOCKS_Y):
        for bx in range(BLOCKS_X):
            x0 = ox + bx * (BLOCK_W + ROAD_W)
            y0 = oy + by * (BLOCK_H + ROAD_W)
            vx = x0 + np.arange(COLS + 1)[None, :] * PARCEL_W + rng.uniform(-0.4, 0.4, (ROWS + 1, COLS + 1))
            vy = y0 + np.arange(ROWS + 1)[:, None] * PARCEL_H + rng.uniform(-0.4, 0.4, (ROWS + 1, COLS + 1))
            for r in range(ROWS):
                for c in range(COLS):
                    ring = [(vx[r, c], vy[r, c]), (vx[r, c + 1], vy[r, c + 1]),
                            (vx[r + 1, c + 1], vy[r + 1, c + 1]), (vx[r + 1, c], vy[r + 1, c])]
                    base.append(Polygon(ring))
                    meta.append({"block": by * BLOCKS_X + bx, "row": r, "col": c})
    n = len(base)
    pids = [f"P{1000 + i}" for i in range(n)]
    survey_no = [100 + i for i in range(n)]
    owners = [f"{FIRST[int(rng.integers(len(FIRST)))]} {LAST[int(rng.integers(len(LAST)))]}" for _ in range(n)]
    land_use = [str(v) for v in rng.choice(LAND_USES, size=n, p=LAND_USE_P)]
    survey_dates = [BASE_DATE + timedelta(days=int(d)) for d in rng.integers(0, 900, n)]

    # ---- disjoint defect pools ----
    order = [int(i) for i in rng.permutation(n)]
    used: set[int] = set()

    def take(k: int, ok=lambda i: True) -> list[int]:
        picked = []
        for i in order:
            if i not in used and ok(i):
                picked.append(i)
                used.add(i)
                if len(picked) == k:
                    break
        return sorted(picked)

    has_right = lambda i: meta[i]["col"] < COLS - 1 and (i + 1) not in used  # noqa: E731
    inj = {
        "invalid_geometry": take(8),
        "overlap": take(12, has_right),
        "gap": take(10, has_right),
    }
    for i in inj["overlap"] + inj["gap"]:
        used.add(i + 1)  # keep the affected neighbour clean of other defects
    inj.update({
        "area_mismatch": take(60),
        "owner_variant": take(50),
        "owner_different": take(25),
        "missing_attribute": take(30),
        "large_shift": take(20),
        "duplicate": take(15),
        "missing_in_municipal": take(15),
    })

    # ---- cadastral (authoritative, EPSG:32643) with topology defects ----
    cad_geoms = list(base)
    for i in inj["invalid_geometry"]:
        a, b, c, d = list(base[i].exterior.coords)[:4]
        cad_geoms[i] = Polygon([a, b, d, c])  # bow-tie
    for i in inj["overlap"]:
        a, b, c, d = list(base[i].exterior.coords)[:4]
        cad_geoms[i] = Polygon([a, (b[0] + 1.5, b[1]), (c[0] + 1.5, c[1]), d])
    for i in inj["gap"]:
        a, b, c, d = (np.array(p) for p in list(base[i].exterior.coords)[:4])
        p1, p2 = b + 0.15 * (c - b), b + 0.85 * (c - b)
        inset = np.array([1.2, 0.0])
        cad_geoms[i] = Polygon([a, b, p1, p1 - inset, p2 - inset, p2, c, d])  # notch -> enclosed gap
    cad_feats = []
    for i in range(n):
        area = round(base[i].area, 1)
        cad_feats.append(_feature({
            "parcel_id": pids[i], "survey_no": survey_no[i], "owner_name": owners[i],
            "area_sqm": area, "land_use": land_use[i], "survey_date": survey_dates[i].isoformat(),
        }, cad_geoms[i], 2))

    # ---- municipal (EPSG:4326, different schema, shifted) ----
    mun_ids = [f"M{7000 + int(v)}" for v in rng.permutation(1000)]
    mid_iter = iter(mun_ids)
    matches: dict[str, str] = {}
    mun_records: list[dict] = []  # {"props", "geom_utm", "parcel"}
    missing = set(inj["missing_in_municipal"])
    for i in range(n):
        if i in missing:
            continue
        g = _shift(base[i], rng, 6, 12) if i in inj["large_shift"] else _shift(base[i], rng, 0.2, 1.5)
        if i in inj["area_mismatch"]:
            f = rng.uniform(1.07, 1.15)
            g = scale(g, np.sqrt(f), np.sqrt(f))
        owner = owners[i]
        if i in inj["owner_variant"]:
            owner = _name_variant(owner, rng)
        elif i in inj["owner_different"]:
            owner = _different_name(owner, rng)
        usage: str | None = land_use[i]
        if i in inj["missing_attribute"]:
            if rng.random() < 0.5:
                owner = None
            else:
                usage = None
        mid = next(mid_iter)
        matches[mid] = pids[i]
        upd = survey_dates[i] + timedelta(days=int(rng.integers(30, 700)))
        mun_records.append({"props": {"Property_ID": mid, "Owner": owner, "Area": round(g.area, 1),
                                      "Usage": usage, "Updated_On": upd.isoformat()},
                            "geom": g, "parcel": i})
    duplicates: dict[str, str] = {}
    for i in inj["duplicate"]:
        g = _shift(base[i], rng, 0.1, 0.5)
        dup_id = next(mid_iter)
        duplicates[dup_id] = pids[i]
        mun_records.append({"props": {"Property_ID": dup_id, "Owner": owners[i], "Area": round(g.area, 1),
                                      "Usage": land_use[i], "Updated_On": survey_dates[i].isoformat()},
                            "geom": g, "parcel": i})

    # ---- municipal v2 (change detection) ----
    v2 = [dict(r, props=dict(r["props"])) for r in mun_records]
    v2_order = [int(k) for k in rng.permutation(len(v2))]
    removed_idx = set(v2_order[:10])
    geom_mod_idx = set(v2_order[10:35])
    attr_mod_idx = set(v2_order[35:65])
    for k in geom_mod_idx:
        v2[k]["geom"] = scale(translate(v2[k]["geom"], 3, 0), 1.1, 1.0)
        v2[k]["props"]["Area"] = round(v2[k]["geom"].area, 1)
    for k in attr_mod_idx:
        p = v2[k]["props"]
        if rng.random() < 0.5 and p["Owner"]:
            p["Owner"] = _different_name(owners[v2[k]["parcel"]], rng)
        else:
            p["Usage"] = "Commercial" if p["Usage"] != "Commercial" else "Mixed Use"
        p["Updated_On"] = "2026-06-30"
    v2_kept = [r for k, r in enumerate(v2) if k not in removed_idx]
    new_y = oy - ROAD_W - PARCEL_H
    new_recs = []
    for k in range(20):
        g = box(ox + k * PARCEL_W, new_y, ox + (k + 1) * PARCEL_W, new_y + PARCEL_H)
        new_recs.append({"props": {"Property_ID": f"M{9000 + k}", "Owner": f"{FIRST[k]} {LAST[k]}",
                                   "Area": round(g.area, 1), "Usage": "Residential", "Updated_On": "2026-06-30"},
                         "geom": g, "parcel": None})
    changes = {
        "NEW": [r["props"]["Property_ID"] for r in new_recs],
        "REMOVED": sorted(v2[k]["props"]["Property_ID"] for k in removed_idx),
        "MODIFIED": sorted(v2[k]["props"]["Property_ID"] for k in geom_mod_idx | attr_mod_idx),
    }

    # ---- revenue (CSV lat/lon points, different schema) ----
    rev_area_mismatch = set(inj["area_mismatch"][:10])
    rev_rows = []
    for i in range(n):
        c = translate(base[i].centroid, *rng.uniform(-1, 1, 2))
        lon, lat = to_ll.transform(c.x, c.y)
        area = base[i].area * (rng.uniform(1.08, 1.14) if i in rev_area_mismatch else 1.0)
        rev_rows.append({"Khasra_No": f"KH-{survey_no[i]}", "Owner_Name": owners[i], "Land_Area": round(area, 1),
                         "Land_Type": land_use[i].upper(), "latitude": f"{lat:.7f}", "longitude": f"{lon:.7f}",
                         "Record_Date": (survey_dates[i] - timedelta(days=int(rng.integers(0, 400)))).isoformat()})

    # ---- buildings ----
    b_feats = []
    bid = 10000
    for i in range(n):
        k = int(rng.choice([0, 1, 2], p=[0.1, 0.3, 0.6]))
        minx, miny, _, _ = base[i].bounds
        rects = [(2, 2, 13, 20)] if k == 1 else [(2, 2, 13, 12), (2, 15, 13, 25)] if k == 2 else []
        for (a, b, c, d) in rects:
            j = rng.uniform(-0.3, 0.3, 2)
            g = box(minx + a + j[0], miny + b + j[1], minx + c + j[0], miny + d + j[1])
            b_feats.append(_feature({"building_id": f"B{bid}", "floors": int(rng.integers(1, 5)),
                                     "use": land_use[i]}, ll(g), 7))
            bid += 1

    # ---- GNSS / ground truthing points ----
    gnss_rows = []
    for k, i in enumerate(sorted(int(v) for v in rng.choice(n, 300, replace=False))):
        x, y = base[i].exterior.coords[0]
        lon, lat = to_ll.transform(x + rng.normal(0, 0.02), y + rng.normal(0, 0.02))
        gnss_rows.append({"survey_id": f"G{2000 + k}", "parcel_ref": pids[i], "accuracy_cm": int(rng.integers(1, 4)),
                          "lat": f"{lat:.7f}", "lon": f"{lon:.7f}",
                          "observed_on": (BASE_DATE + timedelta(days=int(rng.integers(1500, 2600)))).isoformat()})

    # ---- roads ----
    road_feats = []
    width, height = BLOCKS_X * (BLOCK_W + ROAD_W), BLOCKS_Y * (BLOCK_H + ROAD_W)
    for k in range(BLOCKS_Y + 1):
        y = oy - ROAD_W / 2 + k * (BLOCK_H + ROAD_W)
        road_feats.append(_feature({"road_id": f"RH{k}", "name": f"{k + 1} Lane", "width_m": ROAD_W},
                                   ll(LineString([(ox - ROAD_W, y), (ox + width, y)])), 7))
    for k in range(BLOCKS_X + 1):
        x = ox - ROAD_W / 2 + k * (BLOCK_W + ROAD_W)
        road_feats.append(_feature({"road_id": f"RV{k}", "name": f"Road {k + 1}", "width_m": ROAD_W},
                                   ll(LineString([(x, oy - ROAD_W), (x, oy + height)])), 7))

    footprint = mapping(_round(ll(box(ox - ROAD_W, oy - ROAD_W, ox + width, oy + height)), 7))
    registered = [
        {"type": "drone_ori", "name": "Synthetic drone orthomosaic - demo ward (2025)", "resolution": "5 cm GSD",
         "captured_on": "2025-11-12", "crs": "EPSG:32643", "footprint": footprint},
        {"type": "dsm_dtm", "name": "Synthetic DSM / DTM - demo ward", "resolution": "25 cm", "captured_on": "2025-11-12",
         "crs": "EPSG:32643", "footprint": footprint},
        {"type": "utilities", "name": "Synthetic utilities - water and sewer network", "resolution": "vector",
         "captured_on": "2024-03-01", "crs": "EPSG:4326", "footprint": footprint},
    ]

    ground_truth = {
        "matches": dict(sorted(matches.items())),
        "duplicates": dict(sorted(duplicates.items())),
        "injected": {k: [pids[i] for i in v] for k, v in inj.items()},
        "revenue_area_mismatch": [pids[i] for i in sorted(rev_area_mismatch)],
        "changes": changes,
    }

    def mun_fc(recs):
        return _fc([_feature(r["props"], ll(r["geom"]), 7) for r in recs])

    files = {
        "cadastral.geojson": (_fc(cad_feats, 32643), len(cad_feats)),
        "municipal.geojson": (mun_fc(mun_records), len(mun_records)),
        "municipal_v2.geojson": (mun_fc(v2_kept + new_recs), len(v2_kept) + len(new_recs)),
        "buildings.geojson": (_fc(b_feats), len(b_feats)),
        "roads.geojson": (_fc(road_feats), len(road_feats)),
        "registered_sources.json": (json.dumps(registered, indent=1), len(registered)),
        "ground_truth.json": (json.dumps(ground_truth, indent=1), len(matches)),
    }
    for name, (text, _) in files.items():
        (out_dir / name).write_text(text)
    for name, rows in (("revenue.csv", rev_rows), ("gnss.csv", gnss_rows)):
        with open(out_dir / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    summary = {k: v[1] for k, v in files.items()}
    summary["revenue.csv"] = len(rev_rows)
    summary["gnss.csv"] = len(gnss_rows)
    return summary


if __name__ == "__main__":
    from app.config import settings

    print(json.dumps(generate_ward(settings.data_dir), indent=1))
