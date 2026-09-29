from shapely.affinity import scale
from shapely.geometry import Point

from app.engine.conflicts import detect_conflicts
from app.engine.matching import Match, score_pair
from tests.helpers import sq

BASE = {"owner_name": "A B", "land_use": "Residential"}


def m(base_geom, other_geom, base_attrs=BASE, other_attrs=BASE, oid="M1"):
    return Match("P1", oid, score_pair(base_geom, other_geom, base_attrs, other_attrs))


def test_area_mismatch_flagged_with_pct():
    fs = detect_conflicts("P1", BASE, {"municipal": m(sq(0, 0), scale(sq(0, 0), 1.1, 1.0))}, {"municipal": BASE})
    f = next(f for f in fs if f.conflict_type == "AREA_MISMATCH")
    assert "Area differs by 9.1%" in f.explanation and f.source_a == "cadastral" and f.source_b == "municipal"
    assert f.field == "area" and f.observed["a"] == 420.0 and f.observed["b"] == 462.0
    assert f.recommended_action == "Verify with field survey; prefer GNSS-backed area."


def test_owner_variant_not_conflict():
    oa = {"owner_name": "R. Sharma", "land_use": "Residential"}
    ba = {"owner_name": "Rahul Sharma", "land_use": "Residential"}
    fs = detect_conflicts("P1", ba, {"municipal": m(sq(0, 0), sq(0, 0), ba, oa)}, {"municipal": oa})
    assert not any(f.conflict_type == "OWNER_MISMATCH" for f in fs)


def test_owner_mismatch_flagged():
    oa = {"owner_name": "Priya Deshmukh", "land_use": "Residential"}
    ba = {"owner_name": "Rahul Sharma", "land_use": "Residential"}
    f = detect_conflicts("P1", ba, {"municipal": m(sq(0, 0), sq(0, 0), ba, oa)}, {"municipal": oa})[0]
    assert f.conflict_type == "OWNER_MISMATCH" and f.observed == {"a": "Rahul Sharma", "b": "Priya Deshmukh",
                                                                  "delta": f.observed["delta"]}
    assert f.recommended_action == "Manual review required — confirm with revenue record."


def test_missing_attribute_flagged():
    oa = {"owner_name": None, "land_use": "Residential"}
    fs = detect_conflicts("P1", BASE, {"municipal": m(sq(0, 0), sq(0, 0), BASE, oa)}, {"municipal": oa})
    f = next(f for f in fs if f.conflict_type == "MISSING_ATTRIBUTE")
    assert f.field == "owner_name" and f.observed["b"] is None and f.observed["a"] == "A B"


def test_spatial_mismatch_mentions_overlap():
    fs = detect_conflicts("P1", BASE, {"municipal": m(sq(0, 0), sq(8, 0))}, {"municipal": BASE})
    f = next(f for f in fs if f.conflict_type == "SPATIAL_MISMATCH")
    assert "overlap by only" in f.explanation and f.recommended_action == "Manual review required."


def test_revenue_point_outside_parcel_is_spatial_mismatch():
    fs = detect_conflicts("P1", BASE, {"revenue": m(sq(0, 0), Point(40, 40), BASE, {**BASE, "area": 420})},
                          {"revenue": {**BASE, "area": 420}})
    assert any(f.conflict_type == "SPATIAL_MISMATCH" and f.source_b == "revenue" for f in fs)


def test_duplicate_flagged():
    dup = m(sq(0, 0), sq(0.2, 0), oid="M3")
    dup.breakdown.evidence["duplicate_of"] = "M1"
    fs = detect_conflicts("P1", BASE, {"municipal": m(sq(0, 0), sq(0.1, 0))}, {"municipal": BASE}, duplicates=[dup])
    f = next(f for f in fs if f.conflict_type == "DUPLICATE")
    assert f.observed["a"] == "M1" and f.observed["b"] == "M3"
    assert f.recommended_action == "Retain one record; mark the other as duplicate."


def test_clean_match_has_no_conflicts():
    assert detect_conflicts("P1", BASE, {"municipal": m(sq(0, 0), sq(0, 0)), "revenue": None},
                            {"municipal": BASE, "revenue": {}}) == []
