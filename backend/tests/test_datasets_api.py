def test_seeded_datasets_listed(client, seeded):
    ds = client.get("/datasets").json()
    types = {d["source_type"] for d in ds}
    assert {"cadastral", "municipal", "revenue", "buildings", "gnss", "drone_ori", "dsm_dtm", "utilities"} <= types
    cad = next(d for d in ds if d["source_type"] == "cadastral")
    assert cad["record_count"] == 1000 and cad["source_crs"] == "EPSG:32643"
    assert next(d for d in ds if d["source_type"] == "drone_ori")["status"] == "registered"
    assert any(d["source_type"] == "municipal" and d["version"] == 2 for d in ds)


def test_seed_is_idempotent(db_session, seeded, demo_dir):
    from app.models import Dataset, SourceFeature
    from app.seed import seed_demo

    n_ds, n_sf = db_session.query(Dataset).count(), db_session.query(SourceFeature).count()
    seed_demo(db_session, data_dir=demo_dir)
    assert (db_session.query(Dataset).count(), db_session.query(SourceFeature).count()) == (n_ds, n_sf)


def test_upload_geojson(client, seeded, demo_dir):
    with open(demo_dir / "buildings.geojson", "rb") as f:
        r = client.post("/datasets/upload", files={"file": ("b.geojson", f)}, data={"source_type": "buildings"})
    assert r.status_code == 201, r.text
    assert r.json()["record_count"] > 1000 and r.json()["status"] == "ingested"


def test_upload_rejects_bad_extension(client, tmp_path):
    p = tmp_path / "x.exe"
    p.write_bytes(b"MZ")
    r = client.post("/datasets/upload", files={"file": ("x.exe", p.open("rb"))}, data={"source_type": "cadastral"})
    assert r.status_code == 422 and "Unsupported file type" in r.json()["detail"]


def test_upload_rejects_unknown_source_type(client, demo_dir):
    with open(demo_dir / "gnss.csv", "rb") as f:
        r = client.post("/datasets/upload", files={"file": ("g.csv", f)}, data={"source_type": "banana"})
    assert r.status_code == 422


def test_upload_bad_coords_is_422(client, tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("id,lat,lon\n1,2047900,373000\n")
    r = client.post("/datasets/upload", files={"file": ("bad.csv", p.open("rb"))}, data={"source_type": "gnss"})
    assert r.status_code == 422 and "out of range" in r.json()["detail"]
