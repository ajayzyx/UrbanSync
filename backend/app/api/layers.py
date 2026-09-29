import json

import geopandas as gpd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from geoalchemy2.shape import to_shape
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session
from app.engine.changes import detect_changes
from app.models import SRID, Dataset, SourceFeature

router = APIRouter(tags=["layers"])

EMPTY = '{"type":"FeatureCollection","features":[]}'
SIMPLIFY_M = 0.2

FEATURE_SQL = {
    "parcels": f"""
        SELECT json_build_object('type','Feature',
          'geometry', ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(p.geom,{SIMPLIFY_M}),4326),7)::json,
          'properties', json_build_object('parcel_id',p.parcel_id,'match_status',p.match_status,
             'confidence_score',round(p.confidence_score::numeric,3),'topology_status',p.topology_status,
             'owner_name',p.owner_name,'land_use',p.land_use,
             'pending_conflicts',(SELECT count(*) FROM conflicts c WHERE c.canonical_parcel_id=p.id
                                   AND c.status='Pending Review')))
        FROM canonical_parcels p ORDER BY p.parcel_id""",
    "topology": """
        SELECT json_build_object('type','Feature','geometry',ST_AsGeoJSON(ST_Transform(t.geom,4326),7)::json,
          'properties', json_build_object('issue_type',t.issue_type,'detail',t.detail,'fix_status',t.fix_status,
             'parcel_id',p.parcel_id))
        FROM topology_issues t LEFT JOIN canonical_parcels p ON p.id=t.canonical_parcel_id ORDER BY t.id""",
    "conflicts": """
        SELECT json_build_object('type','Feature','geometry',ST_AsGeoJSON(ST_Transform(ST_PointOnSurface(ST_MakeValid(p.geom)),4326),7)::json,
          'properties', json_build_object('parcel_id',p.parcel_id,'count',count(c.id),
             'types',string_agg(DISTINCT c.conflict_type, ',')))
        FROM conflicts c JOIN canonical_parcels p ON p.id=c.canonical_parcel_id
        WHERE c.status='Pending Review' GROUP BY p.id ORDER BY p.parcel_id""",
}
SOURCE_LAYERS = {"municipal", "revenue", "buildings", "gnss", "roads"}


def _fc(rows) -> str:
    return '{"type":"FeatureCollection","features":[' + ",".join(json.dumps(r) for r in rows) + "]}"


def _baseline(session: Session, source_type: str, role: str | None = None) -> Dataset | None:
    for d in session.query(Dataset).filter_by(source_type=source_type).order_by(Dataset.version.desc()):
        if (d.metadata_ or {}).get("role") == role:
            return d
    return None


def _source_layer(session: Session, ds: Dataset) -> str:
    rows = session.execute(text(f"""
        SELECT json_build_object('type','Feature',
          'geometry',ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(geom,{SIMPLIFY_M}),4326),7)::json,
          'properties', json_build_object('record_id',record_id,'valid',geom_valid))
        FROM source_features WHERE dataset_id=:d ORDER BY id"""), {"d": ds.id}).scalars().all()
    return _fc(rows)


def _load(session: Session, ds: Dataset) -> gpd.GeoDataFrame:
    rows = session.query(SourceFeature.record_id, SourceFeature.properties, SourceFeature.geom) \
        .filter_by(dataset_id=ds.id).order_by(SourceFeature.id).all()
    return gpd.GeoDataFrame([{**(p or {}), "_rid": r} for r, p, _ in rows],
                            geometry=[to_shape(g) for *_, g in rows], crs=SRID)


def _changes(session: Session) -> str:
    a, b = _baseline(session, "municipal"), _baseline(session, "municipal", role="update")
    if not a or not b:
        return EMPTY
    recs = detect_changes(_load(session, a), _load(session, b), "_rid")
    gdf = gpd.GeoDataFrame([{"record_id": r.record_id, "change": r.change, "changed_fields": ",".join(r.changed_fields),
                             "geometry_changed": r.geometry_changed} for r in recs],
                           geometry=[r.geom for r in recs], crs=SRID).to_crs(4326)
    return gdf.to_json(drop_id=True)


@router.get("/layers/{layer}")
def get_layer(layer: str, session: Session = Depends(get_session)):
    if layer in FEATURE_SQL:
        body = _fc(session.execute(text(FEATURE_SQL[layer])).scalars().all())
    elif layer in SOURCE_LAYERS:
        ds = _baseline(session, layer)
        body = _source_layer(session, ds) if ds else EMPTY
    elif layer == "changes":
        body = _changes(session)
    else:
        raise HTTPException(404, f"Unknown layer '{layer}'")
    return Response(body, media_type="application/geo+json")
