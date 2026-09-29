import geopandas as gpd

from app.cities import CITIES, get_city
from app.synthetic import generate_ward
from app.validate import validate_city


def test_registry_has_eight_cities_one_demo_one_validation():
    assert len(CITIES) == 8
    assert [c["id"] for c in CITIES if c["status"] == "demo"] == ["pune"]
    assert [c["id"] for c in CITIES if c["status"] == "validation"] == ["surat"]
    assert get_city("mumbai")["state"] == "Maharashtra" and get_city("nowhere") is None


def test_generate_ward_origin_moves_city(tmp_path):
    generate_ward(tmp_path / "a", seed=11, origin_lonlat=(72.8311, 21.1702))
    b = gpd.read_file(tmp_path / "a" / "municipal.geojson").total_bounds
    assert 72.7 < b[0] < 72.95 and 21.0 < b[1] < 21.3


def test_default_demo_ward_unchanged(tmp_path, demo_dir):
    generate_ward(tmp_path)  # defaults must stay byte-identical to the existing demo data
    assert (tmp_path / "ground_truth.json").read_bytes() == (demo_dir / "ground_truth.json").read_bytes()
    assert (tmp_path / "cadastral.geojson").read_bytes() == (demo_dir / "cadastral.geojson").read_bytes()


def test_engine_is_city_agnostic(tmp_path):  # spec §35 — the same model on another city
    r = validate_city("surat", seed=11, out_dir=tmp_path)
    assert r["city"] == "surat" and r["parcels"] == 1000
    assert r["match_precision"] >= 0.97 and r["match_recall"] >= 0.97
    assert r["area_conflict_recall"] >= 0.9 and r["owner_false_positive_rate"] <= 0.06
    assert r["label"] == "Synthetic validation dataset"
    assert (tmp_path / "surat.json").is_file()


def test_cities_endpoint_no_run_has_no_fake_stats(client, seeded):  # Review Focus 1
    cities = {c["id"]: c for c in client.get("/cities").json()}
    assert len(cities) == 8
    pune = cities["pune"]
    assert pune["status"] == "demo" and pune["dataset_label"] == "Demo / Synthetic Dataset"
    assert pune["stats"]["parcels"] == 1000
    assert pune["stats"]["matched"] is None and pune["stats"]["avg_confidence"] is None
    assert pune["test_area"]["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert len(pune["test_area"]["bbox"]) == 4 and 73 < pune["test_area"]["bbox"][0] < 75
    assert cities["mumbai"]["stats"] is None and cities["mumbai"]["test_area"] is None
    assert cities["mumbai"]["dataset_type"] is None


def test_cities_endpoint_after_run_uses_live_numbers(client, seeded):
    assert client.post("/harmonize").status_code in (202, 409)
    pune = client.get("/cities/pune").json()
    assert pune["stats"]["matched"] == 985 and 0.9 < pune["stats"]["avg_confidence"] < 0.98
    assert pune["stats"]["conflicts_pending"] >= 1
    assert client.get("/cities/nowhere").status_code == 404


def test_validation_city_exposed_when_report_exists(client, seeded, tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "validation_dir", tmp_path)
    validate_city("surat", seed=11, out_dir=tmp_path)
    surat = client.get("/cities/surat").json()
    assert surat["dataset_label"] == "Synthetic validation dataset"
    assert surat["validation"]["match_precision"] >= 0.97 and surat["stats"] is None
