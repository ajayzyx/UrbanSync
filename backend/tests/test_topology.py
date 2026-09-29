import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

from app.engine.topology import validate_topology
from app.ingest.normalize import normalize
from app.ingest.readers import read_source


def test_bowtie_self_intersection_suggested_fix():
    bow = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
    g = gpd.GeoDataFrame({"pid": ["P1"]}, geometry=[bow], crs=32643)
    f = validate_topology(g, "pid")[0]
    assert f.issue_type == "SELF_INTERSECTION" and f.suggested_fix.is_valid and f.fix_status == "requires_review"
    assert f.detail.endswith("Correction suggested — requires review.")
    assert not g.geometry.iloc[0].is_valid  # input untouched


def test_overlap_detected():
    g = gpd.GeoDataFrame({"pid": ["P1", "P2"]}, geometry=[box(0, 0, 10, 10), box(8.5, 0, 20, 10)], crs=32643)
    f = next(f for f in validate_topology(g, "pid") if f.issue_type == "OVERLAP")
    assert f.location.area == pytest.approx(15.0) and "requires review" in f.detail
    assert f.parcel_id == "P1" and f.related == ["P2"]


def test_gap_detected():
    cells = [box(x * 10, y * 10, x * 10 + 10, y * 10 + 10) for y in range(3) for x in range(3)]
    cells[4] = box(10, 10, 19, 20)
    g = gpd.GeoDataFrame({"pid": [f"P{i}" for i in range(9)]}, geometry=cells, crs=32643)
    gaps = [f for f in validate_topology(g, "pid") if f.issue_type == "GAP"]
    assert len(gaps) == 1 and gaps[0].location.area == pytest.approx(10.0)
    assert gaps[0].parcel_id is None and "P4" in gaps[0].related and "P5" in gaps[0].related


def test_clean_grid_has_no_findings():
    cells = [box(x * 10, 0, x * 10 + 10, 10) for x in range(4)]
    assert validate_topology(gpd.GeoDataFrame({"pid": list("abcd")}, geometry=cells, crs=32643), "pid") == []


def test_synthetic_ward_topology_counts(demo_dir):
    cad = normalize(read_source(demo_dir / "cadastral.geojson")[0]).gdf
    fs = validate_topology(cad, "parcel_id")
    assert sum(f.issue_type in ("SELF_INTERSECTION", "INVALID_GEOMETRY") for f in fs) == 8
    assert sum(f.issue_type == "OVERLAP" for f in fs) >= 12
    assert sum(f.issue_type == "GAP" for f in fs) >= 10
