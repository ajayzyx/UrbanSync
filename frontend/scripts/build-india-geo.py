"""One-time build of the vendored India geography (run from backend/: uv run python ../frontend/scripts/build-india-geo.py <shp_dir>).

Source: DataMeet community maps (https://github.com/datameet/maps), CC-BY 4.0.
Outputs (committed):
  frontend/public/geo/india-states.json  — simplified state polygons for the interactive map
  frontend/public/geo/india-hero.json    — single SVG path + registry city positions for the landing hero
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.cities import CITIES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "public" / "geo"
shp = Path(sys.argv[1]) / "Admin2.shp"

g = gpd.read_file(shp).rename(columns={"ST_NM": "name"})
g["geometry"] = g.geometry.simplify(0.02, preserve_topology=True)
g["geometry"] = shapely.set_precision(g.geometry.values, 1e-4)  # ~11 m; rounds coords to 4 dp
g = g[~g.geometry.is_empty]
OUT.mkdir(parents=True, exist_ok=True)
g.to_file(OUT / "india-states.json", driver="GeoJSON", COORDINATE_PRECISION=4)

# hero snapshot: equirectangular projection into a 1000-wide viewBox, one path per country
minx, miny, maxx, maxy = g.total_bounds
W = 1000.0
sx = W / (maxx - minx)
H = round((maxy - miny) * sx, 1)
coarse = g.geometry.simplify(0.06, preserve_topology=True)


def ring_to_path(ring) -> str:
    pts = [f"{(x - minx) * sx:.1f},{(maxy - y) * sx:.1f}" for x, y in ring.coords]
    return "M" + "L".join(pts) + "Z"


d = "".join(ring_to_path(p.exterior) for geom in coarse for p in getattr(geom, "geoms", [geom]))
cities = [{"id": c["id"], "name": c["name"], "status": c["status"],
           "x": round((c["lon"] - minx) * sx, 1), "y": round((maxy - c["lat"]) * sx, 1)} for c in CITIES]
(OUT / "india-hero.json").write_text(json.dumps({"w": W, "h": H, "states": d, "cities": cities}))
print(f"states: {len(g)} features, {(OUT / 'india-states.json').stat().st_size / 1024:.0f} KB")
print(f"hero: {(OUT / 'india-hero.json').stat().st_size / 1024:.0f} KB, viewBox 1000x{H}")
