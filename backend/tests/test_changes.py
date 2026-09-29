import json

import geopandas as gpd

from app.engine.changes import detect_changes
from app.ingest.normalize import normalize
from app.ingest.readers import read_source
from tests.helpers import sq


def test_changes_match_ground_truth(demo_dir):
    a = normalize(read_source(demo_dir / "municipal.geojson")[0]).gdf
    b = normalize(read_source(demo_dir / "municipal_v2.geojson")[0]).gdf
    gt = json.loads((demo_dir / "ground_truth.json").read_text())["changes"]
    rs = {r.record_id: r for r in detect_changes(a, b, "Property_ID")}
    assert {k for k, r in rs.items() if r.change == "NEW"} == set(gt["NEW"])
    assert {k for k, r in rs.items() if r.change == "REMOVED"} == set(gt["REMOVED"])
    assert {k for k, r in rs.items() if r.change == "MODIFIED"} == set(gt["MODIFIED"])


def test_attribute_only_change_and_nan_equal_none():
    a = gpd.GeoDataFrame({"id": ["A", "B"], "owner": ["X", None]}, geometry=[sq(0, 0), sq(20, 0)], crs=32643)
    b = gpd.GeoDataFrame({"id": ["A", "B"], "owner": ["Y", float("nan")]}, geometry=[sq(0, 0), sq(20, 0)], crs=32643)
    rs = {r.record_id: r for r in detect_changes(a, b, "id")}
    assert rs["A"].change == "MODIFIED" and rs["A"].changed_fields == ["owner"] and not rs["A"].geometry_changed
    assert rs["B"].change == "UNCHANGED"
