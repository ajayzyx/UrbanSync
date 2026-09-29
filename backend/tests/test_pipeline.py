import json

import pytest

from app.models import CanonicalParcel, Conflict, FeatureMatch, HarmonizationRun, SourceFeature
from app.pipeline import RunInProgress, run_harmonization, start_run


@pytest.fixture(scope="module")
def completed_run(db_session, seeded, session_factory):
    run = start_run(db_session)
    run_harmonization(run.id, session_factory)
    db_session.expire_all()
    return db_session.get(HarmonizationRun, run.id)


def test_full_run_summary(completed_run):
    run = completed_run
    assert run.status == "completed", run.error
    assert [s["status"] for s in run.stages] == ["done"] * 7
    assert [s["key"] for s in run.stages] == ["ingest", "normalize", "match", "attributes", "validate", "resolve", "harmonize"]
    s = run.summary
    assert s["parcels"] == 1000 and s["matched"] >= 970
    assert 0.80 <= s["avg_confidence"] <= 0.98
    assert s["conflicts"] > 0 and s["topology_issues"] >= 30
    assert {"dataset": "municipal", "from": "EPSG:4326", "to": "EPSG:32643"} in s["crs_transforms"]
    assert s["changes"] == {"NEW": 20, "REMOVED": 10, "MODIFIED": 55, "UNCHANGED": 935}


def test_stage_details_are_truthful(completed_run):
    by = {s["key"]: s for s in completed_run.stages}
    assert "EPSG:4326 → EPSG:32643" in by["normalize"]["detail"]
    assert "985 municipal" in by["match"]["detail"]
    assert all(s["started_at"] and s["finished_at"] for s in completed_run.stages)


def test_conflict_detection_recall_vs_ground_truth(completed_run, db_session, demo_dir):
    gt = json.loads((demo_dir / "ground_truth.json").read_text())["injected"]
    flagged = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="AREA_MISMATCH")}
    assert len(flagged & set(gt["area_mismatch"])) / len(gt["area_mismatch"]) >= 0.9
    owner = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="OWNER_MISMATCH")}
    assert len(owner & set(gt["owner_variant"])) <= 3  # name variants must not be treated as conflicts
    assert len(owner & set(gt["owner_different"])) >= 20
    dups = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="DUPLICATE")}
    assert dups == set(gt["duplicate"])


def test_provenance_kept(completed_run, db_session):
    p = db_session.query(CanonicalParcel).filter_by(parcel_id="P1023").one()
    assert {"cadastral", "revenue"} <= {x["source_type"] for x in p.provenance}
    assert all("record_id" in x and "dataset_id" in x for x in p.provenance)


def test_matches_persisted_with_components(completed_run, db_session):
    fm = db_session.query(FeatureMatch).filter_by(source_type="municipal").first()
    assert fm.geometry_score is not None and "Reason:" in fm.explanation and fm.match_class in {"HIGH", "REVIEW", "CONFLICT"}


def test_source_features_untouched_by_run(completed_run, db_session):
    assert db_session.query(SourceFeature).filter_by(geom_valid=False).count() == 8


def test_rerun_replaces_derived_rows(completed_run, db_session, session_factory):  # Review Focus 2
    r = start_run(db_session)
    run_harmonization(r.id, session_factory)
    db_session.expire_all()
    assert db_session.query(CanonicalParcel).count() == 1000
    assert db_session.query(HarmonizationRun).count() == 2


def test_start_run_rejects_concurrent(db_session, seeded):
    db_session.add(HarmonizationRun(status="running", stages=[], summary={}))
    db_session.commit()
    with pytest.raises(RunInProgress):
        start_run(db_session)
    db_session.query(HarmonizationRun).filter_by(status="running").delete()
    db_session.commit()


def test_concurrent_run_rejected_via_api(client, db_session, seeded):
    db_session.add(HarmonizationRun(status="running", stages=[], summary={}))
    db_session.commit()
    r = client.post("/harmonize")
    assert r.status_code == 409 and "already in progress" in r.json()["detail"]
    db_session.query(HarmonizationRun).filter_by(status="running").delete()
    db_session.commit()


def test_run_endpoint_shape(client, seeded):
    rid = client.post("/harmonize").json()["run_id"]  # TestClient runs background tasks before returning
    body = client.get(f"/harmonization/{rid}").json()
    assert body["status"] == "completed" and body["stages"][0]["key"] == "ingest"
    assert client.get("/harmonization/latest").json()["id"] == rid
    assert client.get("/harmonization/999999").status_code == 404


def test_mappings_endpoint(client, completed_run):
    latest = client.get("/harmonization/latest").json()["id"]  # derived rows belong to the latest run only
    rows = client.get(f"/harmonization/{latest}/mappings").json()
    assert rows, "mappings should be persisted"
    owner = [r for r in rows if r["source_field"] == "Owner_Name"]
    assert owner and owner[0]["canonical_field"] == "owner_name" and owner[0]["confidence"] >= 0.9


def test_no_area_conflict_for_invalid_cadastral_geometry(completed_run, db_session, demo_dir):
    # area of a self-intersecting ring is undefined; the TOPOLOGY conflict covers it
    invalid = set(json.loads((demo_dir / "ground_truth.json").read_text())["injected"]["invalid_geometry"])
    area = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="AREA_MISMATCH")}
    topo = {c.parcel.parcel_id for c in db_session.query(Conflict).filter_by(conflict_type="TOPOLOGY")}
    assert not (area & invalid) and invalid <= topo


def test_municipal_matches_carry_advisory_ml_probability(completed_run, db_session):
    fms = db_session.query(FeatureMatch).filter_by(source_type="municipal").all()
    probs = [m.evidence.get("ml_probability") for m in fms]
    assert all(p is not None and 0 <= p <= 1 for p in probs)
    # the weighted score is still the source of truth
    assert all(m.final_confidence is not None for m in fms)
