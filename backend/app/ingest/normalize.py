from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd

from app.config import settings
from app.ingest.readers import _epsg


@dataclass
class NormalizeResult:
    gdf: gpd.GeoDataFrame
    source_crs: str
    target_crs: str
    invalid_count: int
    empty_count: int


def normalize(gdf: gpd.GeoDataFrame, target_crs: str | None = None) -> NormalizeResult:
    """Reproject to the project CRS. Geometry is validated and counted, never repaired here."""
    target_crs = target_crs or settings.project_crs
    source = _epsg(gdf.crs)
    out = gdf.to_crs(target_crs) if source != target_crs else gdf.copy()
    empty = int(out.geometry.is_empty.sum() + out.geometry.isna().sum())
    invalid = int((~out.geometry.is_valid & ~out.geometry.is_empty).sum())
    return NormalizeResult(out, source, target_crs, invalid, empty)
