"""Map heterogeneous department schemas onto canonical parcel fields, with a confidence per mapping."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

import pandas as pd
from rapidfuzz import fuzz

CANONICAL_FIELDS = ["parcel_id", "source_property_id", "owner_name", "area", "land_use", "survey_date"]

SYNONYMS: dict[str, list[str]] = {
    "parcel_id": ["parcel_id", "parcel_no", "khasra_no", "khasra", "survey_no", "cts_no", "plot_no"],
    "source_property_id": ["property_id", "prop_id", "property_no", "upic", "assessment_no"],
    "owner_name": ["owner_name", "owner", "owners", "owner_nm", "holder_name", "khatedar"],
    "area": ["area", "land_area", "area_sqm", "area_sq_m", "plot_area", "shape_area"],
    "land_use": ["land_use", "landuse", "usage", "land_type", "property_use", "use_type", "zone"],
    "survey_date": ["survey_date", "updated_on", "record_date", "last_updated", "observed_on"],
}
SKIP = {"geometry", "lat", "lon", "lng", "latitude", "longitude", "x", "y"}
FUZZY_MIN = 80

Method = Literal["synonym", "fuzzy", "value_profile", "unmapped"]


@dataclass
class FieldMapping:
    source_field: str
    canonical_field: str | None
    confidence: float
    method: Method


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _profile_fits(canonical: str, values: pd.Series) -> bool:
    v = values.dropna()
    if v.empty:
        return False
    if canonical == "area":
        return pd.api.types.is_numeric_dtype(v)
    if canonical == "owner_name":
        s = v.astype(str)
        return bool((s.str.split().str.len() >= 2).mean() > 0.6 and s.str.contains(r"[A-Za-z]").all())
    if canonical == "land_use":
        return v.astype(str).nunique() <= 10
    return False


def map_fields(df: pd.DataFrame) -> list[FieldMapping]:
    out: list[FieldMapping] = []
    for col in df.columns:
        key = _key(str(col))
        if key in SKIP:
            continue
        canonical, conf, method = None, 0.0, "unmapped"
        for field, syns in SYNONYMS.items():
            if key == field:
                canonical, conf, method = field, 1.0, "synonym"
                break
            if key in syns:
                canonical, conf, method = field, 0.95, "synonym"
                break
        if canonical is None:
            flat = key.replace("_", "")
            best = max(((f, max(fuzz.ratio(flat, s.replace("_", "")) for s in syns)) for f, syns in SYNONYMS.items()),
                       key=lambda t: t[1])
            if best[1] >= FUZZY_MIN:
                canonical, conf, method = best[0], round(best[1] / 100 * 0.9, 3), "fuzzy"
        if canonical and _profile_fits(canonical, df[col]):
            conf = min(1.0, round(conf + 0.05, 3))
        out.append(FieldMapping(str(col), canonical, conf, method))
    return out


def _none(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def _norm_value(field: str, v):
    v = _none(v)
    if v is None:
        return None
    if field == "area":
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    if field == "owner_name":
        s = " ".join(str(v).split())
        return s or None
    if field == "land_use":
        return str(v).strip().title() or None
    return str(v).strip() if isinstance(v, str) else v


def apply_mapping(df: pd.DataFrame, mappings: list[FieldMapping]) -> pd.DataFrame:
    """Return a frame with exactly CANONICAL_FIELDS; the highest-confidence source column wins per field."""
    chosen: dict[str, FieldMapping] = {}
    for m in mappings:
        if m.canonical_field and (m.canonical_field not in chosen or m.confidence > chosen[m.canonical_field].confidence):
            chosen[m.canonical_field] = m
    out = pd.DataFrame(index=df.index)
    for field in CANONICAL_FIELDS:
        m = chosen.get(field)
        vals = [_norm_value(field, v) for v in df[m.source_field]] if m else [None] * len(df)
        out[field] = pd.Series(vals, index=df.index, dtype=object)
    return out


def normalize_name(s: str | None) -> str:
    if not s:
        return ""
    tokens = re.sub(r"[^a-z ]+", " ", str(s).lower()).split()
    return " ".join(sorted(tokens))


def name_similarity(a: str | None, b: str | None) -> float | None:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return None
    return round(fuzz.token_set_ratio(na, nb) / 100, 4)
