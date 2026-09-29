"""Read uploaded / demo files into GeoDataFrames and detect their CRS. Files are parsed, never executed."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError

ALLOWED_EXTENSIONS = {".geojson", ".json", ".csv", ".zip"}
LAT_NAMES = ("lat", "latitude", "y")
LON_NAMES = ("lon", "lng", "long", "longitude", "x")


class IngestError(ValueError):
    pass


def sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-. ]", "_", str(name))[:120]


def _epsg(crs) -> str:
    epsg = CRS.from_user_input(crs).to_epsg()
    return f"EPSG:{epsg}" if epsg else CRS.from_user_input(crs).to_string()


def _check_geographic(gdf: gpd.GeoDataFrame) -> None:
    if gdf.empty:
        return
    minx, miny, maxx, maxy = gdf.total_bounds
    if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
        raise IngestError("Coordinates out of range for EPSG:4326 — supply crs (e.g. EPSG:32643)")


def _read_csv(path: Path, crs_hint: str | None) -> gpd.GeoDataFrame:
    df = pd.read_csv(path)
    lower = {c.lower().strip(): c for c in df.columns}
    lat = next((lower[n] for n in LAT_NAMES if n in lower), None)
    lon = next((lower[n] for n in LON_NAMES if n in lower), None)
    if not lat or not lon:
        raise IngestError("CSV must contain latitude/longitude columns (lat/latitude/y and lon/lng/longitude/x)")
    xs, ys = pd.to_numeric(df[lon], errors="coerce"), pd.to_numeric(df[lat], errors="coerce")
    if xs.isna().any() or ys.isna().any():
        raise IngestError("CSV latitude/longitude columns contain non-numeric values")
    gdf = gpd.GeoDataFrame(df.drop(columns=[lat, lon]), geometry=gpd.points_from_xy(xs, ys),
                           crs=crs_hint or "EPSG:4326")
    return gdf


PROJECT_AREA_MARGIN_DEG = 0.5


def _check_project_area(gdf: gpd.GeoDataFrame) -> None:
    """Reject data that cannot belong to the project's UTM zone (swapped lat/lon, wrong CRS hint)."""
    from app.config import settings

    if gdf.empty:
        return
    west, south, east, north = CRS.from_user_input(settings.project_crs).area_of_use.bounds
    m = PROJECT_AREA_MARGIN_DEG
    minx, miny, maxx, maxy = Transformer.from_crs(gdf.crs, 4326, always_xy=True).transform_bounds(*gdf.total_bounds)
    if minx < west - m or maxx > east + m or miny < south - m or maxy > north + m:
        raise IngestError(
            f"Coordinates fall outside the project area ({settings.project_crs}, lon {west:.0f}–{east:.0f}°E) "
            f"— are latitude/longitude swapped, or is the CRS wrong?")


def read_source(path: Path, crs_hint: str | None = None) -> tuple[gpd.GeoDataFrame, str]:
    path = Path(path)
    if crs_hint:
        try:
            CRS.from_user_input(crs_hint)
        except CRSError as exc:
            raise IngestError(f"Unrecognised CRS '{sanitize(crs_hint)}' — use a code such as EPSG:4326") from exc
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise IngestError(f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    try:
        if ext == ".csv":
            gdf = _read_csv(path, crs_hint)
        elif ext == ".zip":
            with zipfile.ZipFile(path) as zf:
                shp = next((n for n in zf.namelist() if n.lower().endswith(".shp")), None)
            if not shp:
                raise IngestError("ZIP does not contain a .shp file")
            gdf = gpd.read_file(f"/vsizip/{path}/{shp}")
        else:
            gdf = gpd.read_file(path)
    except IngestError:
        raise
    except Exception as exc:  # parser errors -> clean 422
        raise IngestError(f"Could not parse file: {exc}") from exc

    if crs_hint:
        gdf = gdf.set_crs(crs_hint, allow_override=True)
    elif gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    if gdf.crs.is_geographic:
        _check_geographic(gdf)
    _check_project_area(gdf)
    gdf.columns = [sanitize(c) if c != gdf.geometry.name else c for c in gdf.columns]
    return gdf, _epsg(gdf.crs)
