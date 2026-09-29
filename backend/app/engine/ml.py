"""Advisory ML match classifier (logistic regression on the six component scores).

Trained on a *different* synthetic ward (seed 7) than the demo ward (seed 42), so its agreement with the
weighted baseline is an independent check. The weighted score remains the source of final_confidence.
"""

from __future__ import annotations

import json
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.engine.matching import COMPONENTS, ScoreBreakdown, candidate_pairs
from app.ingest.normalize import normalize
from app.ingest.readers import read_source

TRAIN_SEED = 7

__all__ = ["candidate_pairs", "features", "get_model", "ml_probability", "train_classifier"]


def features(b: ScoreBreakdown) -> list[float]:
    vals = [getattr(b, c) for c in COMPONENTS]
    return [0.5 if v is None else float(v) for v in vals] + [1.0 if v is None else 0.0 for v in vals]


def train_classifier(pairs: list[ScoreBreakdown], labels: list[int]) -> LogisticRegression:
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(np.array([features(b) for b in pairs]), np.array(labels))
    return model


@lru_cache(maxsize=1)
def get_model() -> LogisticRegression:
    from app.synthetic import generate_ward

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        generate_ward(d, seed=TRAIN_SEED)
        cad = normalize(read_source(d / "cadastral.geojson")[0]).gdf
        mun = normalize(read_source(d / "municipal.geojson")[0]).gdf
        gt = json.loads((d / "ground_truth.json").read_text())
    truth = {**gt["matches"], **gt["duplicates"]}
    pairs = candidate_pairs(cad, mun, "parcel_id", "Property_ID")
    return train_classifier([b for *_, b in pairs], [int(truth.get(o) == p) for p, o, _ in pairs])


def ml_probability(model: LogisticRegression, b: ScoreBreakdown) -> float:
    return round(float(model.predict_proba(np.array([features(b)]))[0, 1]), 4)
