import json

from app.engine.matching import score_pair
from app.engine.ml import candidate_pairs, features, get_model, ml_probability
from app.ingest.normalize import normalize
from app.ingest.readers import read_source
from tests.helpers import sq


def test_features_encode_missing_components():
    b = score_pair(sq(0, 0), sq(0, 0), {}, {})
    f = features(b)
    assert len(f) == 12 and f[6 + 4] == 1.0  # attribute missing flag


def test_probability_in_unit_interval():
    m = get_model()
    p = ml_probability(m, score_pair(sq(0, 0), sq(0.5, 0), {"owner_name": "A B"}, {"owner_name": "A B"}))
    assert 0.0 <= p <= 1.0 and p > 0.5


def test_model_trained_on_other_ward_generalises(demo_dir):
    # trained on seed 7, evaluated on the seed-42 demo ward's answer key
    cad = normalize(read_source(demo_dir / "cadastral.geojson")[0]).gdf
    mun = normalize(read_source(demo_dir / "municipal.geojson")[0]).gdf
    gt = json.loads((demo_dir / "ground_truth.json").read_text())
    truth = {**gt["matches"], **gt["duplicates"]}
    m = get_model()
    best: dict[str, tuple[float, str]] = {}
    for base_id, other_id, b in candidate_pairs(cad, mun, "parcel_id", "Property_ID"):
        p = ml_probability(m, b)
        if p >= 0.5 and p > best.get(base_id, (0, ""))[0]:
            best[base_id] = (p, other_id)
    correct = sum(truth.get(o) == pid for pid, (_, o) in best.items())
    assert correct / len(best) >= 0.97
