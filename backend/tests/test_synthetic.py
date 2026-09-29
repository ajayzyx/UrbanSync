import json

import geopandas as gpd

from app.synthetic import generate_ward


def test_generate_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generate_ward(a)
    generate_ward(b)
    for f in ["cadastral.geojson", "municipal.geojson", "municipal_v2.geojson", "revenue.csv", "ground_truth.json"]:
        assert (a / f).read_bytes() == (b / f).read_bytes(), f


def test_counts_and_crs(tmp_path):
    summary = generate_ward(tmp_path)
    assert summary["cadastral.geojson"] == 1000
    assert 1400 <= summary["buildings.geojson"] <= 1600
    cad = gpd.read_file(tmp_path / "cadastral.geojson")
    assert cad.crs.to_epsg() == 32643
    assert gpd.read_file(tmp_path / "municipal.geojson").crs.to_epsg() == 4326
    assert cad["parcel_id"].iloc[0] == "P1000"


def test_ground_truth_injections(tmp_path):
    generate_ward(tmp_path)
    gt = json.loads((tmp_path / "ground_truth.json").read_text())
    assert len(gt["injected"]["area_mismatch"]) == 60
    assert len(gt["injected"]["invalid_geometry"]) == 8
    assert len(gt["matches"]) == 1000 - 15  # missing_in_municipal excluded, duplicates not in matches
    cad = gpd.read_file(tmp_path / "cadastral.geojson")
    assert (~cad.geometry.is_valid).sum() == 8


def test_registered_sources_and_changes(tmp_path):
    generate_ward(tmp_path)
    reg = json.loads((tmp_path / "registered_sources.json").read_text())
    assert {r["type"] for r in reg} == {"drone_ori", "dsm_dtm", "utilities"}
    ch = json.loads((tmp_path / "ground_truth.json").read_text())["changes"]
    assert (len(ch["NEW"]), len(ch["REMOVED"]), len(ch["MODIFIED"])) == (20, 10, 55)
