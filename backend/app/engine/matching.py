"""Spatial matching with an explainable, weighted confidence score.

All geometry must be in metres (project CRS). Input geometries are never modified.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry

from app.config import settings
from app.engine.attributes import apply_mapping, map_fields, name_similarity

WEIGHTS: dict[str, float] = dict(settings.weights)
COMPONENTS = ["geometry", "centroid", "area", "shape", "attribute", "temporal"]
DIST_SCALE_M = 10.0  # centroid / boundary deviation at which the score falls to 1/e
AREA_SENSITIVITY = 4.0  # 10 % area difference -> 0.6, 25 % -> 0
TEMPORAL_HORIZON_DAYS = 3650

MatchClass = Literal["HIGH", "REVIEW", "CONFLICT"]
REASONS = {
    "HIGH": "The two features represent the same spatial parcel with strong geometric and attribute agreement.",
    "REVIEW": "Likely the same parcel, but some evidence disagrees — reviewer confirmation recommended.",
    "CONFLICT": "Evidence is contradictory; manual review required before these records are linked.",
}
CLASS_LABEL = {"HIGH": "HIGH-CONFIDENCE MATCH", "REVIEW": "REVIEW", "CONFLICT": "CONFLICT"}


@dataclass
class ScoreBreakdown:
    geometry: float | None
    centroid: float | None
    area: float | None
    shape: float | None
    attribute: float | None
    temporal: float | None
    final: float
    match_class: str
    evidence: dict = field(default_factory=dict)

    def components(self) -> dict[str, float | None]:
        return {c: getattr(self, c) for c in COMPONENTS}


@dataclass
class Match:
    base_id: str
    other_id: str
    breakdown: ScoreBreakdown


def classify(final: float) -> MatchClass:
    if final >= settings.high_threshold:
        return "HIGH"
    if final >= settings.review_threshold:
        return "REVIEW"
    return "CONFLICT"


def _valid(g: BaseGeometry) -> BaseGeometry:
    return g if g.is_valid else shapely.make_valid(g)


def _clip(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def _date(v) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def _num(v) -> float | None:
    try:
        f = float(v)
        return None if math.isnan(f) or f <= 0 else f
    except (TypeError, ValueError):
        return None


def score_pair(base_geom: BaseGeometry, other_geom: BaseGeometry, base_attrs: dict, other_attrs: dict) -> ScoreBreakdown:
    a, b = _valid(base_geom), _valid(other_geom)
    ev: dict = {"iou": None, "centroid_distance_m": None, "area_diff_pct": None, "hausdorff_m": None,
                "name_similarity": None, "date_gap_days": None, "point_in_polygon": None}
    s: dict[str, float | None] = dict.fromkeys(COMPONENTS)

    is_point = b.geom_type in ("Point", "MultiPoint")
    if is_point:
        inside = bool(a.covers(b))
        ev["point_in_polygon"] = inside
        s["geometry"] = 1.0 if inside else 0.0
        area_a, area_b = a.area, _num(other_attrs.get("area"))
    else:
        inter = a.intersection(b).area
        union = a.area + b.area - inter
        iou = inter / union if union > 0 else 0.0
        ev["iou"] = round(iou, 4)
        s["geometry"] = _clip(iou)
        h = shapely.hausdorff_distance(a, b)
        ev["hausdorff_m"] = round(h, 2)
        s["shape"] = _clip(math.exp(-h / DIST_SCALE_M))
        area_a, area_b = a.area, b.area

    d = a.centroid.distance(b.centroid)
    ev["centroid_distance_m"] = round(d, 3)
    s["centroid"] = _clip(math.exp(-d / DIST_SCALE_M))

    if area_a and area_b:
        diff = abs(area_a - area_b) / max(area_a, area_b)
        ev["area_diff_pct"] = round(diff * 100, 2)
        ev["area_a_sqm"], ev["area_b_sqm"] = round(area_a, 1), round(area_b, 1)
        s["area"] = _clip(1 - AREA_SENSITIVITY * diff)

    sim = name_similarity(base_attrs.get("owner_name"), other_attrs.get("owner_name"))
    ev["name_similarity"] = sim
    s["attribute"] = sim

    da, db = _date(base_attrs.get("survey_date")), _date(other_attrs.get("survey_date"))
    if da and db:
        gap = abs((db - da).days)
        ev["date_gap_days"] = gap
        s["temporal"] = _clip(1 - gap / TEMPORAL_HORIZON_DAYS)

    num = sum(WEIGHTS[k] * v for k, v in s.items() if v is not None)
    den = sum(WEIGHTS[k] for k, v in s.items() if v is not None)
    final = round(num / den, 4) if den else 0.0
    rounded = {k: (round(v, 4) if v is not None else None) for k, v in s.items()}
    return ScoreBreakdown(**rounded, final=final, match_class=classify(final), evidence=ev)


def _mark(score: float | None) -> str:
    if score is None:
        return "·"
    return "✓" if score >= 0.8 else "!" if score < 0.6 else "·"


def explain(b: ScoreBreakdown, base_id: str, other_id: str, other_label: str) -> str:
    ev = b.evidence
    lines = [f"Parcel {base_id} ↔ {other_label} {other_id}"]
    if ev.get("point_in_polygon") is not None:
        lines.append(f"{_mark(b.geometry)} Record location {'falls inside' if ev['point_in_polygon'] else 'lies outside'} the parcel boundary")
    elif ev.get("iou") is not None:
        lines.append(f"{_mark(b.geometry)} {ev['iou']:.0%} boundary overlap (IoU)")
    if ev.get("centroid_distance_m") is not None:
        lines.append(f"{_mark(b.centroid)} {ev['centroid_distance_m']:.1f} m centroid distance")
    if ev.get("area_diff_pct") is not None:
        lines.append(f"{_mark(b.area)} {ev['area_diff_pct']:.1f}% area difference")
    if ev.get("hausdorff_m") is not None:
        lines.append(f"{_mark(b.shape)} {ev['hausdorff_m']:.1f} m max boundary deviation")
    if ev.get("name_similarity") is not None:
        lines.append(f"{_mark(b.attribute)} {ev['name_similarity']:.0%} owner-name similarity")
    else:
        lines.append("· Owner name not available in both sources (not applicable)")
    if ev.get("date_gap_days") is not None:
        lines.append(f"{_mark(b.temporal)} {ev['date_gap_days']} days between record dates")
    lines.append(f"Overall confidence: {b.final:.0%} — {CLASS_LABEL[b.match_class]}")
    lines.append(f"Reason: {REASONS[b.match_class]}")
    return "\n".join(lines)


def _attrs(gdf: gpd.GeoDataFrame) -> list[dict]:
    df = gdf.drop(columns=[gdf.geometry.name])
    return apply_mapping(df, map_fields(df)).to_dict("records")


def _scored_candidates(base: gpd.GeoDataFrame, other: gpd.GeoDataFrame, max_distance_m: float
                       ) -> list[tuple[float, int, int, ScoreBreakdown]]:
    bg = [_valid(g) for g in base.geometry]
    og = [_valid(g) for g in other.geometry]
    battrs, oattrs = _attrs(base), _attrs(other)
    bc = np.array([(g.centroid.x, g.centroid.y) for g in bg])
    oc = np.array([(g.centroid.x, g.centroid.y) for g in og])
    tree = shapely.STRtree(og)
    base_idx, other_idx = tree.query(shapely.points(bc), predicate="dwithin", distance=max_distance_m)
    pairs: list[tuple[float, int, int, ScoreBreakdown]] = []
    for i, j in zip(base_idx, other_idx):
        if np.hypot(*(bc[i] - oc[j])) > max_distance_m:
            continue
        b = score_pair(bg[i], og[j], battrs[i], oattrs[j])
        pairs.append((b.final, int(i), int(j), b))
    pairs.sort(key=lambda t: (-t[0], t[1], t[2]))
    return pairs


def candidate_pairs(base: gpd.GeoDataFrame, other: gpd.GeoDataFrame, base_id_col: str, other_id_col: str,
                    max_distance_m: float = 15.0) -> list[tuple[str, str, ScoreBreakdown]]:
    """Every scored candidate pair within range (before one-to-one assignment)."""
    base, other = base.reset_index(drop=True), other.reset_index(drop=True)
    return [(str(base.at[i, base_id_col]), str(other.at[j, other_id_col]), b)
            for _, i, j, b in _scored_candidates(base, other, max_distance_m)]


def match_layers(base: gpd.GeoDataFrame, other: gpd.GeoDataFrame, base_id_col: str, other_id_col: str,
                 max_distance_m: float = 15.0) -> list[Match]:
    """One-to-one greedy assignment by descending confidence; leftover near-identical features become duplicates."""
    base = base.reset_index(drop=True)
    other = other.reset_index(drop=True)
    pairs = _scored_candidates(base, other, max_distance_m)

    used_b: dict[int, int] = {}
    used_o: set[int] = set()
    out: list[Match] = []
    for final, i, j, b in pairs:
        if i in used_b or j in used_o:
            continue
        used_b[i] = j
        used_o.add(j)
        out.append(Match(str(base.at[i, base_id_col]), str(other.at[j, other_id_col]), b))
    for final, i, j, b in pairs:
        if j in used_o or i not in used_b or b.evidence.get("iou") is None or b.evidence["iou"] < 0.8:
            continue
        used_o.add(j)
        b.evidence["duplicate_of"] = str(other.at[used_b[i], other_id_col])
        out.append(Match(str(base.at[i, base_id_col]), str(other.at[j, other_id_col]), b))
    return out
