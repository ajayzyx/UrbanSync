from __future__ import annotations

import math

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import DISCLAIMER
from app.engine.attributes import apply_mapping, map_fields
from app.models import CanonicalParcel, Conflict, FeatureMatch, SourceFeature

COMPONENT_COLS = {"geometry": "geometry_score", "centroid": "centroid_score", "area": "area_score",
                  "shape": "shape_score", "attribute": "attribute_score", "temporal": "temporal_score"}
SOURCE_LABEL = {"cadastral": "Cadastral", "municipal": "Municipal", "revenue": "Revenue", "gnss": "GNSS",
                "buildings": "Building footprints"}
def clean(v):
    """Recursively make a value JSON-safe (NaN/inf -> None)."""
    if isinstance(v, float):
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    return v


def geojson(session: Session, geom, precision: int = 7):
    import json

    return json.loads(session.scalar(select(func.ST_AsGeoJSON(func.ST_Transform(geom, 4326), precision))))


def bbox(session: Session, geom) -> list[float]:
    g = func.ST_Transform(geom, 4326)
    row = session.execute(select(func.ST_XMin(g), func.ST_YMin(g), func.ST_XMax(g), func.ST_YMax(g))).one()
    return [round(x, 7) for x in row]


def canonical_values(props: dict) -> dict:
    df = pd.DataFrame([props or {}])
    return clean(apply_mapping(df, map_fields(df)).iloc[0].to_dict())


def source_values(session: Session, parcel: CanonicalParcel) -> dict[str, dict]:
    """Canonical-field view of each primary source record linked to the parcel (side-by-side comparison)."""
    out: dict[str, dict] = {}
    for p in parcel.provenance:
        if p["source_type"] in ("cadastral", "municipal", "revenue") and p["source_type"] not in out:
            sf = session.get(SourceFeature, p["source_feature_id"])
            if sf:
                vals = {**canonical_values(sf.properties), "record_id": sf.record_id}
                if vals.get("survey_date"):
                    vals["survey_date"] = str(vals["survey_date"])[:10]
                gtype, area = session.execute(select(func.ST_GeometryType(sf.geom),
                                                     func.ST_Area(func.ST_MakeValid(sf.geom)))).one()
                if "Polygon" in gtype:  # show the mapped area the detector compared; keep the recorded one alongside
                    vals["recorded_area"] = vals.get("area")
                    vals["area"] = round(area, 1)
                out[p["source_type"]] = vals
    return out


def conflict_out(session: Session, c: Conflict, with_values: bool = False) -> dict:
    d = {"id": c.id, "parcel_id": c.parcel.parcel_id, "conflict_type": c.conflict_type, "source_a": c.source_a,
         "source_b": c.source_b, "field": c.field, "observed": c.observed, "confidence": c.confidence,
         "explanation": c.explanation, "recommended_action": c.recommended_action, "status": c.status,
         "resolution": c.resolution, "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None}
    if with_values:
        d["source_values"] = source_values(session, c.parcel)
        d["bbox"] = bbox(session, c.parcel.geom)
        d["disclaimer"] = DISCLAIMER
    return clean(d)


def match_out(m: FeatureMatch) -> dict:
    return clean({"id": m.id, "source_type": m.source_type, "record_id": m.source_feature.record_id,
                  "components": {k: getattr(m, col) for k, col in COMPONENT_COLS.items()},
                  "final_confidence": m.final_confidence, "match_class": m.match_class, "evidence": m.evidence,
                  "explanation": m.explanation, "is_duplicate": "duplicate_of" in (m.evidence or {})})


def parcel_summary(session: Session, p: CanonicalParcel, box: list[float] | None = None) -> dict:
    return clean({"parcel_id": p.parcel_id, "owner_name": p.owner_name, "area": p.area, "land_use": p.land_use,
                  "confidence_score": p.confidence_score, "match_status": p.match_status,
                  "topology_status": p.topology_status, "source_count": p.source_count,
                  "conflict_count": sum(1 for c in p.conflicts if c.status == "Pending Review"),
                  "bbox": box if box is not None else bbox(session, p.geom)})


def parcel_detail(session: Session, p: CanonicalParcel) -> dict:
    d = parcel_summary(session, p)
    d.update({
        "geometry": geojson(session, p.geom),
        "provenance": [{**x, "label": SOURCE_LABEL.get(x["source_type"], x["source_type"])} for x in p.provenance],
        "matches": [match_out(m) for m in sorted(p.matches, key=lambda m: ("duplicate_of" in (m.evidence or {}),
                                                                         m.source_type != "municipal"))],
        "source_values": source_values(session, p),
        "conflicts": [conflict_out(session, c) for c in sorted(p.conflicts, key=lambda c: c.id)],
        "topology": [{"issue_type": t.issue_type, "detail": t.detail, "fix_status": t.fix_status} for t in p.topology],
        "resolved_values": p.resolved_values or {}, "building_count": p.building_count, "gnss_count": p.gnss_count,
        "last_updated": p.last_updated.isoformat() if p.last_updated else None, "disclaimer": DISCLAIMER,
    })
    return clean(d)
