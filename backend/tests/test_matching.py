import json
import math

import geopandas as gpd
import pytest
from shapely.affinity import scale
from shapely.geometry import Point

from app.engine.matching import WEIGHTS, classify, explain, match_layers, score_pair
from app.ingest.normalize import normalize
from app.ingest.readers import read_source
from tests.helpers import sq


def test_identical_parcels_high():
    b = score_pair(sq(0, 0), sq(0, 0), {"owner_name": "Rahul Sharma", "area": 420},
                   {"owner_name": "SHARMA RAHUL", "area": 420})
    assert b.final >= 0.95 and b.match_class == "HIGH"


def test_small_shift_still_high():
    b = score_pair(sq(0, 0), sq(1.0, 0.5), {"owner_name": "A B"}, {"owner_name": "A B"})
    assert b.match_class == "HIGH" and b.evidence["centroid_distance_m"] == pytest.approx(1.118, abs=0.01)


def test_area_mismatch_drops_to_review():
    b = score_pair(sq(0, 0), scale(sq(0, 0), 1.12, 1.12), {"owner_name": "A B"}, {"owner_name": "A B"})
    assert b.match_class == "REVIEW"
    assert b.evidence["area_diff_pct"] == pytest.approx(20.3, abs=0.2)


def test_far_different_owner_conflict():
    b = score_pair(sq(0, 0), sq(10, 8), {"owner_name": "Rahul Sharma"}, {"owner_name": "Priya Deshmukh"})
    assert b.match_class == "CONFLICT"


def test_missing_components_renormalized():  # Review Focus 4
    b = score_pair(sq(0, 0), Point(7.5, 14), {"area": 420}, {"area": 420})
    assert b.geometry == 1.0 and b.shape is None and b.attribute is None and b.temporal is None
    assert not math.isnan(b.final) and b.final >= 0.85
    assert b.evidence["point_in_polygon"] is True


def test_invalid_base_geometry_does_not_crash():
    from shapely.geometry import Polygon

    bow = Polygon([(0, 0), (15, 28), (15, 0), (0, 28)])
    b = score_pair(bow, sq(0, 0), {}, {})
    assert not math.isnan(b.final) and b.match_class in {"REVIEW", "CONFLICT"}


def test_temporal_component():
    b = score_pair(sq(0, 0), sq(0, 0), {"survey_date": "2020-01-01"}, {"survey_date": "2021-01-01"})
    assert b.temporal == pytest.approx(1 - 366 / 3650, abs=1e-3) and b.evidence["date_gap_days"] == 366


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_classify_thresholds():
    assert (classify(0.85), classify(0.8499), classify(0.6), classify(0.5999)) == ("HIGH", "REVIEW", "REVIEW", "CONFLICT")


def test_explanation_lists_evidence():
    b = score_pair(sq(0, 0), sq(0.5, 0), {"owner_name": "A B"}, {"owner_name": "A B"})
    text = explain(b, "P1023", "M7781", "Municipal")
    assert "P1023 ↔ Municipal M7781" in text and "overlap" in text and "Reason:" in text
    assert "✓" in text and "Overall confidence" in text


def test_match_layers_one_to_one_and_duplicate():
    base = gpd.GeoDataFrame({"pid": ["P1", "P2"]}, geometry=[sq(0, 0), sq(20, 0)], crs=32643)
    other = gpd.GeoDataFrame({"mid": ["M1", "M2", "M3"]}, geometry=[sq(0.5, 0), sq(20.3, 0), sq(0.2, 0)], crs=32643)
    ms = match_layers(base, other, "pid", "mid")
    primary = [m for m in ms if "duplicate_of" not in m.breakdown.evidence]
    assert sorted((m.base_id, m.other_id) for m in primary) in ([("P1", "M3"), ("P2", "M2")],
                                                                [("P1", "M1"), ("P2", "M2")])
    dup = [m for m in ms if "duplicate_of" in m.breakdown.evidence]
    assert len(dup) == 1 and dup[0].base_id == "P1"


def test_accuracy_against_ground_truth(demo_dir):
    cad = normalize(read_source(demo_dir / "cadastral.geojson")[0]).gdf
    mun = normalize(read_source(demo_dir / "municipal.geojson")[0]).gdf
    gt = json.loads((demo_dir / "ground_truth.json").read_text())
    truth = {**gt["matches"], **gt["duplicates"]}
    ms = [m for m in match_layers(cad, mun, "parcel_id", "Property_ID") if "duplicate_of" not in m.breakdown.evidence]
    correct = sum(truth.get(m.other_id) == m.base_id for m in ms)
    assert correct / len(gt["matches"]) >= 0.97 and correct / len(ms) >= 0.97
    classes = [m.breakdown.match_class for m in ms]
    assert classes.count("HIGH") / len(ms) > 0.7
