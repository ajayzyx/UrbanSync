"""Regression tests for the whole-branch review findings."""

import threading

import pytest

from app.ingest.normalize import normalize
from app.ingest.readers import IngestError, read_source
from app.models import CanonicalParcel, Conflict, HarmonizationRun
from app.pipeline import RunInProgress, recover_interrupted_runs, run_harmonization, start_run


# --- I1: swapped / mis-declared coordinates -------------------------------------------------
def test_swapped_latlon_csv_rejected(tmp_path):
    p = tmp_path / "swapped.csv"
    p.write_text("id,lat,lon\n1,73.875,18.531\n")
    with pytest.raises(IngestError, match="outside the project area"):
        read_source(p)


def test_latlon_csv_with_utm_crs_hint_rejected(tmp_path):
    p = tmp_path / "ll.csv"
    p.write_text("id,lat,lon\n1,18.531,73.875\n")
    with pytest.raises(IngestError, match="outside the project area"):
        read_source(p, crs_hint="EPSG:32643")


def test_correct_latlon_csv_still_accepted(tmp_path):
    p = tmp_path / "ok.csv"
    p.write_text("id,lat,lon\n1,18.531,73.875\n")
    assert normalize(read_source(p)[0]).gdf.total_bounds[0] > 300_000


# --- I7: invalid CRS hint -> 422, never 500 ----------------------------------------------------
def test_invalid_crs_hint_is_ingest_error(demo_dir):
    with pytest.raises(IngestError, match="Unrecognised CRS"):
        read_source(demo_dir / "roads.geojson", crs_hint="foo")


def test_upload_with_invalid_crs_is_422(client, seeded, demo_dir):
    with open(demo_dir / "roads.geojson", "rb") as f:
        r = client.post("/datasets/upload", files={"file": ("r.geojson", f)}, data={"source_type": "roads", "crs": "foo"})
    assert r.status_code == 422 and "CRS" in r.json()["detail"]


# --- I6: interrupted runs are recovered on startup ----------------------------------------------
def test_recover_interrupted_runs(db_session, seeded):
    db_session.add(HarmonizationRun(status="running", stages=[], summary={}))
    db_session.commit()
    assert recover_interrupted_runs(db_session) == 1
    assert db_session.query(HarmonizationRun).filter_by(status="running").count() == 0
    db_session.query(HarmonizationRun).delete()
    db_session.commit()


# --- I5: concurrent starts cannot both run ---------------------------------------------------
def test_concurrent_start_run_only_one_wins(session_factory, seeded):
    results, barrier = [], threading.Barrier(2)

    def go():
        s = session_factory()
        barrier.wait()
        try:
            results.append(start_run(s).id)
        except RunInProgress:
            results.append("409")
        finally:
            s.close()

    ts = [threading.Thread(target=go) for _ in range(2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    try:
        assert sorted(map(str, results)).count("409") == 1
    finally:
        s = session_factory()
        s.query(HarmonizationRun).delete()
        s.commit()
        s.close()


@pytest.fixture(scope="module")
def harmonized(client, seeded):
    assert client.post("/harmonize").status_code == 202
    return client


# --- I3: never resolve to an empty value ------------------------------------------------------
def test_resolve_with_null_source_value_rejected(harmonized):
    c = next(c for c in harmonized.get("/conflicts", params={"type": "attribute", "limit": 500}).json()
             if c["conflict_type"] == "MISSING_ATTRIBUTE")
    r = harmonized.post(f"/conflicts/{c['id']}/resolve", json={"status": "Resolved", "chosen_source": c["source_b"]})
    assert r.status_code == 422 and "no value" in r.json()["detail"]


def test_resolve_uses_conflict_field_not_request_field(harmonized):
    c = harmonized.get("/conflicts", params={"type": "attribute", "limit": 500}).json()
    c = next(x for x in c if x["conflict_type"] == "OWNER_MISMATCH" and x["status"] == "Pending Review")
    before = harmonized.get(f"/parcels/{c['parcel_id']}").json()["area"]
    r = harmonized.post(f"/conflicts/{c['id']}/resolve",
                        json={"status": "Resolved", "chosen_source": "cadastral", "field": "area"})
    assert r.status_code == 200 and r.json()["area"] == before and "owner_name" in r.json()["resolved_values"]


# --- I4: resolving never beats the match class -------------------------------------------------
def test_conflict_class_parcel_not_promoted(harmonized):
    p = harmonized.get("/parcels", params={"status": "CONFLICT", "limit": 1}).json()[0]
    for c in harmonized.get(f"/parcels/{p['parcel_id']}").json()["conflicts"]:
        if c["status"] == "Pending Review":
            harmonized.post(f"/conflicts/{c['id']}/resolve", json={"status": "Accepted"})
    assert harmonized.get(f"/parcels/{p['parcel_id']}").json()["match_status"] == "CONFLICT"


def _parcel(final, *conflicts):
    from types import SimpleNamespace as NS

    return NS(matches=[NS(final_confidence=final, evidence={})],
              conflicts=[NS(conflict_type=t, status=st) for t, st in conflicts])


def test_derive_status_rules():
    from app.review import derive_status

    # REVIEW by score only: resolving a non-blocking conflict must not promote
    assert derive_status(_parcel(0.72, ("MISSING_ATTRIBUTE", "Resolved"))) == "REVIEW"
    # reviewer confirms the blocking discrepancy of a REVIEW-class parcel -> reviewer-confirmed
    assert derive_status(_parcel(0.80, ("AREA_MISMATCH", "Resolved"))) == "HARMONIZED"
    # Ignored never confirms
    assert derive_status(_parcel(0.80, ("AREA_MISMATCH", "Ignored"))) == "REVIEW"
    # CONFLICT class is never promoted
    assert derive_status(_parcel(0.40, ("SPATIAL_MISMATCH", "Accepted"))) == "CONFLICT"
    # pending blocking conflict caps a HIGH parcel at REVIEW
    assert derive_status(_parcel(0.95, ("TOPOLOGY", "Pending Review"))) == "REVIEW"
    assert derive_status(_parcel(0.95)) == "HARMONIZED"


def test_ignore_does_not_promote(harmonized):
    c = harmonized.get("/conflicts", params={"type": "area", "status": "Pending Review"}).json()
    c = next(x for x in c if len(harmonized.get(f"/parcels/{x['parcel_id']}").json()["conflicts"]) == 1)
    harmonized.post(f"/conflicts/{c['id']}/resolve", json={"status": "Ignored"})
    assert harmonized.get(f"/parcels/{c['parcel_id']}").json()["match_status"] != "HARMONIZED"


# --- I2: reviewer decisions survive a rerun -----------------------------------------------------
def test_rerun_preserves_reviewer_decisions(harmonized, session_factory, db_session):
    c = harmonized.get("/conflicts", params={"type": "area", "status": "Pending Review"}).json()[0]
    r = harmonized.post(f"/conflicts/{c['id']}/resolve",
                        json={"status": "Resolved", "chosen_source": "cadastral", "note": "GNSS confirms"}).json()
    status_before = r["match_status"]
    run = start_run(db_session)
    run_harmonization(run.id, session_factory)
    after = harmonized.get(f"/parcels/{c['parcel_id']}").json()
    assert after["resolved_values"]["area"]["note"] == "GNSS confirms"
    assert after["match_status"] == status_before
    area = [x for x in after["conflicts"] if x["conflict_type"] == "AREA_MISMATCH"]
    assert area and all(x["status"] == "Resolved" for x in area)
    assert db_session.query(CanonicalParcel).filter_by(parcel_id=c["parcel_id"]).count() == 1


# --- upgraded minors ---------------------------------------------------------------------------
def test_resolve_during_run_is_409(harmonized, db_session):
    c = harmonized.get("/conflicts", params={"status": "Pending Review"}).json()[0]
    db_session.add(HarmonizationRun(status="running", stages=[], summary={}))
    db_session.commit()
    try:
        assert harmonized.post(f"/conflicts/{c['id']}/resolve", json={"status": "Accepted"}).status_code == 409
    finally:
        db_session.query(HarmonizationRun).filter_by(status="running").delete()
        db_session.commit()


def test_cadastral_only_run_completes(db_session, session_factory, demo_dir):
    from sqlalchemy import text

    from app.ingest.store import ingest_file

    db_session.execute(text("TRUNCATE topology_issues, conflicts, feature_matches, attribute_mappings, "
                            "canonical_parcels, harmonization_runs, source_features, datasets RESTART IDENTITY CASCADE"))
    db_session.expunge_all()
    ingest_file(db_session, demo_dir / "cadastral.geojson", "cadastral", "cad only")
    db_session.commit()
    run = start_run(db_session)
    run_harmonization(run.id, session_factory)
    db_session.expire_all()
    run = db_session.get(HarmonizationRun, run.id)
    assert run.status == "completed", run.error
    assert run.summary["unmatched"] == 1000
    assert db_session.query(Conflict).filter(Conflict.conflict_type != "TOPOLOGY").count() == 0
