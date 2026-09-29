def test_health_reports_db_and_postgis(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["postgis"].startswith("3.")
    assert body["project_crs"] == "EPSG:32643"


def test_cors_allows_any_local_port(client):
    r = client.get("/health", headers={"Origin": "http://localhost:3210"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3210"
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers
