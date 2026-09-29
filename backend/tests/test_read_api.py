import json

import pytest

from app.models import SourceFeature


@pytest.fixture(scope="module")
def ready(client, seeded):
    assert client.post("/harmonize").status_code == 202
    return client


def test_empty_state_before_run(client, seeded):
    # runs before `ready` (module order): no run yet -> empty but well-formed responses
    assert client.get("/parcels").json() == []
    assert client.get("/layers/parcels").json() == {"type": "FeatureCollection", "features": []}
    a = client.get("/analytics").json()
    assert a["run"] is None and a["kpis"]["parcels"] == 0


def test_parcel_detail_explainable(ready):
    d = ready.get("/parcels/P1023").json()
    assert d["parcel_id"] == "P1023" and d["geometry"]["type"] == "Polygon"
    m = d["matches"][0]
    assert set(m["components"]) == {"geometry", "centroid", "area", "shape", "attribute", "temporal"}
    assert "Reason:" in m["explanation"] and "not a legal determination" in d["disclaimer"]
    assert {"cadastral", "municipal", "revenue"} <= set(d["source_values"])
    assert d["source_values"]["revenue"]["parcel_id"].startswith("KH-")
    assert any(p["source_type"] == "cadastral" for p in d["provenance"])


def test_point_match_components_not_applicable(ready):  # Review Focus 4
    d = ready.get("/parcels/P1023").json()
    rev = next(m for m in d["matches"] if m["source_type"] == "revenue")
    assert rev["components"]["shape"] is None


def test_no_nan_in_json(ready):  # Review Focus 4
    for path in ["/layers/parcels", "/parcels?limit=1000", "/analytics", "/conflicts"]:
        txt = ready.get(path).text
        assert "NaN" not in txt and "Infinity" not in txt, path


def test_search_by_id_owner_and_khasra(ready):
    assert ready.get("/parcels", params={"q": "P1023"}).json()[0]["parcel_id"] == "P1023"
    assert len(ready.get("/parcels", params={"q": "KH-"}).json()) > 0
    owner = ready.get("/parcels/P1023").json()["owner_name"].split()[-1]
    assert len(ready.get("/parcels", params={"q": owner.lower()}).json()) > 0
    s = ready.get("/parcels", params={"q": "P1023"}).json()[0]
    assert len(s["bbox"]) == 4 and 73 < s["bbox"][0] < 75


def test_parcel_status_filter(ready):
    rows = ready.get("/parcels", params={"status": "REVIEW", "limit": 1000}).json()
    assert rows and {r["match_status"] for r in rows} == {"REVIEW"}


def test_conflict_filter_alias(ready):
    rows = ready.get("/conflicts", params={"type": "attribute"}).json()
    assert rows and {r["conflict_type"] for r in rows} <= {"OWNER_MISMATCH", "MISSING_ATTRIBUTE"}
    topo = ready.get("/conflicts", params={"type": "topology"}).json()
    assert topo and {r["conflict_type"] for r in topo} == {"TOPOLOGY"}


def test_conflict_detail_has_source_values(ready):
    c = ready.get("/conflicts", params={"type": "area"}).json()[0]
    d = ready.get(f"/conflicts/{c['id']}").json()
    assert d["source_values"]["cadastral"]["area"] is not None and d["parcel_id"] == c["parcel_id"]


def test_resolve_updates_canonical_not_source(ready, db_session):  # Review Focus 3
    c = ready.get("/conflicts", params={"type": "area"}).json()[0]
    snap = lambda: [(f.id, json.dumps(f.properties, sort_keys=True), bytes(f.geom.data))  # noqa: E731
                    for f in db_session.query(SourceFeature).order_by(SourceFeature.id)]
    before = snap()
    r = ready.post(f"/conflicts/{c['id']}/resolve",
                   json={"status": "Resolved", "chosen_source": "cadastral", "field": "area", "note": "GNSS confirms"})
    assert r.status_code == 200, r.text
    rv = r.json()["resolved_values"]["area"]
    assert rv["resolved_by"] == "reviewer" and rv["source"] == "cadastral" and rv["note"] == "GNSS confirms"
    db_session.expire_all()
    assert snap() == before
    assert ready.get(f"/conflicts/{c['id']}").json()["status"] == "Resolved"


def test_resolving_all_conflicts_harmonizes_parcel(ready):
    pid = ready.get("/conflicts", params={"type": "area", "status": "Pending Review"}).json()[0]["parcel_id"]
    for c in ready.get("/parcels/" + pid).json()["conflicts"]:
        if c["status"] == "Pending Review":
            body = {"status": "Resolved", "chosen_source": "cadastral"} if c["field"] else {"status": "Accepted"}
            assert ready.post(f"/conflicts/{c['id']}/resolve", json=body).status_code == 200
    assert ready.get("/parcels/" + pid).json()["match_status"] == "HARMONIZED"


def test_resolve_value_conflict_requires_source(ready):
    c = ready.get("/conflicts", params={"type": "area", "status": "Pending Review"}).json()[0]
    assert ready.post(f"/conflicts/{c['id']}/resolve", json={"status": "Resolved"}).status_code == 422


def test_resolve_rejects_bad_status(ready):
    c = ready.get("/conflicts").json()[0]
    assert ready.post(f"/conflicts/{c['id']}/resolve", json={"status": "Done"}).status_code == 422
    assert ready.post("/conflicts/999999/resolve", json={"status": "Ignored"}).status_code == 404


def test_layers(ready):
    for layer in ["parcels", "municipal", "revenue", "buildings", "gnss", "roads", "topology", "conflicts", "changes"]:
        fc = ready.get(f"/layers/{layer}").json()
        assert fc["type"] == "FeatureCollection" and fc["features"], layer
    assert ready.get("/layers/nope").status_code == 404
    ch = {f["properties"]["change"] for f in ready.get("/layers/changes").json()["features"]}
    assert {"NEW", "MODIFIED", "REMOVED"} <= ch
    lon, lat = ready.get("/layers/parcels").json()["features"][0]["geometry"]["coordinates"][0][0]
    assert 73 < lon < 75 and 18 < lat < 19


def test_parcels_layer_payload_small(ready):
    assert len(ready.get("/layers/parcels").content) < 1_500_000


def test_analytics(ready):
    a = ready.get("/analytics").json()
    assert a["kpis"]["parcels"] == 1000 and a["evaluation"]["match_precision"] >= 0.97
    assert a["evaluation"]["area_conflict_recall"] >= 0.9
    assert any(r["metric"] == "Distinct CRS" and r["after"] == 1 for r in a["quality_before_after"])
    assert sum(b["count"] for b in a["confidence_histogram"]) == 1000
    assert {m["class"] for m in a["match_distribution"]} >= {"HARMONIZED", "REVIEW"}
    assert a["run"]["status"] == "completed"


def test_unknown_parcel_404(ready):
    assert ready.get("/parcels/P9999").status_code == 404


def test_conflict_side_by_side_shows_compared_areas(ready):
    for c in ready.get("/conflicts", params={"type": "area"}).json()[:20]:
        d = ready.get(f"/conflicts/{c['id']}").json()
        sv = d["source_values"]
        assert sv["cadastral"]["area"] == pytest.approx(c["observed"]["a"], abs=0.2)
        assert sv[c["source_b"]]["area"] == pytest.approx(c["observed"]["b"], abs=0.2)
        assert "recorded_area" in sv["cadastral"]


def test_analytics_reports_ml_agreement(ready):
    ev = ready.get("/analytics").json()["evaluation"]
    assert ev["ml_match_precision"] >= 0.97 and 0 <= ev["ml_baseline_agreement"] <= 1
