"""Deterministic version-to-version change detection (A vs B) keyed on a record id."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import geopandas as gpd
import shapely
from shapely.geometry.base import BaseGeometry


@dataclass
class ChangeRecord:
    record_id: str
    change: Literal["NEW", "MODIFIED", "REMOVED", "UNCHANGED"]
    geometry_changed: bool
    changed_fields: list[str] = field(default_factory=list)
    iou: float | None = None
    geom: BaseGeometry | None = None


def _norm(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def _iou(a: BaseGeometry, b: BaseGeometry) -> float:
    a, b = shapely.make_valid(a), shapely.make_valid(b)
    inter = a.intersection(b).area
    union = a.area + b.area - inter
    return inter / union if union else 1.0


def detect_changes(a: gpd.GeoDataFrame, b: gpd.GeoDataFrame, id_col: str,
                   iou_threshold: float = 0.95) -> list[ChangeRecord]:
    ga, gb = a.geometry.name, b.geometry.name
    ra = {str(r[id_col]): r for _, r in a.iterrows()}
    rb = {str(r[id_col]): r for _, r in b.iterrows()}
    cols = [c for c in b.columns if c not in (gb, id_col) and c in a.columns]
    out: list[ChangeRecord] = []
    for rid in sorted(set(ra) | set(rb)):
        if rid not in ra:
            out.append(ChangeRecord(rid, "NEW", True, [], None, rb[rid][gb]))
        elif rid not in rb:
            out.append(ChangeRecord(rid, "REMOVED", True, [], None, ra[rid][ga]))
        else:
            iou = _iou(ra[rid][ga], rb[rid][gb])
            geom_changed = iou < iou_threshold
            changed = [c for c in cols if _norm(ra[rid][c]) != _norm(rb[rid][c])]
            kind = "MODIFIED" if geom_changed or changed else "UNCHANGED"
            out.append(ChangeRecord(rid, kind, geom_changed, changed, round(iou, 4), rb[rid][gb]))
    return out
