"""Topology validation. Findings carry suggested fixes; source geometry is never modified."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import geopandas as gpd
import shapely
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

REVIEW = "Correction suggested — requires review."


@dataclass
class TopologyFinding:
    parcel_id: str | None
    issue_type: str
    location: BaseGeometry
    detail: str
    suggested_fix: BaseGeometry | None
    fix_status: Literal["auto_safe", "requires_review"]
    related: list[str] = field(default_factory=list)


def _largest_polygon(g: BaseGeometry) -> BaseGeometry | None:
    polys = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"]
    if not polys:
        polys = [q for p in getattr(g, "geoms", [g]) for q in getattr(p, "geoms", []) if q.geom_type == "Polygon"]
    return max(polys, key=lambda p: p.area) if polys else None


def _ring_area(g: BaseGeometry) -> float:
    return abs(Polygon(g.exterior.coords).area) if g.geom_type == "Polygon" else g.area


def validate_topology(gdf: gpd.GeoDataFrame, id_col: str, min_overlap_sqm: float = 0.5,
                      max_gap_sqm: float = 200.0) -> list[TopologyFinding]:
    ids = [str(v) for v in gdf[id_col]]
    geoms = list(gdf.geometry)
    out: list[TopologyFinding] = []

    valid: list[BaseGeometry] = []
    for pid, g in zip(ids, geoms):
        if g.is_valid:
            valid.append(g)
            continue
        reason = shapely.is_valid_reason(g)
        kind = "SELF_INTERSECTION" if "Self-intersection" in reason else "INVALID_GEOMETRY"
        fixed = _largest_polygon(shapely.make_valid(g))
        original = _ring_area(g)
        safe = fixed is not None and original > 0 and abs(fixed.area - original) / original <= 0.01
        detail = f"{reason}." + ("" if safe else f" {REVIEW}")
        loc = g.envelope if g.geom_type != "Point" else g
        out.append(TopologyFinding(pid, kind, loc, detail.strip(), fixed, "auto_safe" if safe else "requires_review"))
        valid.append(fixed if fixed is not None else shapely.make_valid(g))

    tree = shapely.STRtree(valid)
    left, right = tree.query(valid, predicate="intersects")
    for i, j in zip(left, right):
        if i >= j:
            continue
        inter = valid[i].intersection(valid[j])
        if inter.area > min_overlap_sqm and (geoms[i].is_valid and geoms[j].is_valid):
            out.append(TopologyFinding(ids[i], "OVERLAP", inter,
                                       f"{ids[i]} overlaps {ids[j]} by {inter.area:.1f} m². {REVIEW}",
                                       None, "requires_review", [ids[j]]))

    union = shapely.unary_union([g for g, orig in zip(valid, geoms) if orig.is_valid])
    for poly in getattr(union, "geoms", [union]):
        for ring in getattr(poly, "interiors", []):
            hole = Polygon(ring)
            if 1.0 < hole.area <= max_gap_sqm:
                touching = [ids[k] for k in tree.query(hole.buffer(0.1), predicate="intersects")
                            if geoms[k].is_valid]
                out.append(TopologyFinding(None, "GAP", hole,
                                           f"Unassigned gap of {hole.area:.1f} m² between parcels. {REVIEW}",
                                           None, "requires_review", sorted(touching)))
    return out
