"""Persist a normalized GeoDataFrame as an (immutable) dataset of source features."""

from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
from geoalchemy2.shape import from_shape
from shapely.geometry import box
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.ingest.normalize import normalize
from app.ingest.readers import read_source, sanitize
from app.models import SRID, Dataset, SourceFeature

SOURCE_TYPES = {"cadastral", "municipal", "revenue", "buildings", "gnss", "roads", "drone_ori", "dsm_dtm", "utilities"}
ID_COLUMNS = ("parcel_id", "Property_ID", "Khasra_No", "building_id", "survey_id", "road_id")


def clean_value(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if hasattr(v, "item"):  # numpy scalar
        return clean_value(v.item())
    return v


def _records(gdf: gpd.GeoDataFrame) -> list[dict]:
    cols = [c for c in gdf.columns if c != gdf.geometry.name]
    return [{c: clean_value(row[c]) for c in cols} for _, row in gdf.iterrows()]


def ingest_gdf(session: Session, gdf: gpd.GeoDataFrame, source_type: str, name: str, file_name: str,
               source_crs: str | None = None, version: int = 1) -> Dataset:
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unknown source_type '{source_type}'")
    res = normalize(gdf)
    g = res.gdf
    id_col = next((c for c in ID_COLUMNS if c in g.columns), None)
    props = _records(g)
    ds = Dataset(name=sanitize(name), source_type=source_type, version=version, file_name=sanitize(file_name),
                 source_crs=source_crs or res.source_crs, record_count=len(g), status="ingested",
                 fields=[c for c in g.columns if c != g.geometry.name],
                 metadata_={"invalid_geometries": res.invalid_count, "empty_geometries": res.empty_count},
                 footprint=from_shape(box(*g.total_bounds), srid=SRID) if len(g) else None)
    session.add(ds)
    session.flush()
    rows = []
    for i, (geom, p) in enumerate(zip(g.geometry, props)):
        if geom is None or geom.is_empty:
            continue
        rows.append({"dataset_id": ds.id, "record_id": str(p.get(id_col)) if id_col else str(i),
                     "properties": p, "geom": from_shape(geom, srid=SRID), "geom_valid": bool(geom.is_valid)})
    if rows:
        session.execute(insert(SourceFeature), rows)
    return ds


def ingest_file(session: Session, path: Path, source_type: str, name: str, crs_hint: str | None = None,
                version: int = 1, file_name: str | None = None) -> Dataset:
    gdf, crs = read_source(path, crs_hint)
    return ingest_gdf(session, gdf, source_type, name, file_name or Path(path).name, crs, version)


def register_source(session: Session, entry: dict) -> Dataset:
    fp = gpd.GeoDataFrame.from_features([{"type": "Feature", "properties": {}, "geometry": entry["footprint"]}],
                                        crs="EPSG:4326").to_crs(SRID)
    ds = Dataset(name=entry["name"], source_type=entry["type"], version=1, file_name=None,
                 source_crs=entry.get("crs"), record_count=0, status="registered", fields=[],
                 metadata_={k: entry[k] for k in ("resolution", "captured_on") if k in entry},
                 footprint=from_shape(fp.geometry.iloc[0], srid=SRID))
    session.add(ds)
    return ds


def dataset_metadata_json(ds: Dataset) -> str:
    return json.dumps(ds.metadata_)
