"""Run the UNCHANGED harmonization engine against a second synthetic city (spec v2 §35).

Proves the model is city-agnostic: same schema, same pipeline, different geography and seed.
CLI: `python -m app.validate` -> data/validation/<city>.json for every validation-status city.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.cities import CITIES, get_city
from app.engine.conflicts import detect_conflicts
from app.engine.matching import match_layers
from app.ingest.normalize import normalize
from app.ingest.readers import read_source
from app.synthetic import generate_ward

VALIDATION_SEED = 11


def _attrs(gdf, id_col: str) -> dict[str, dict]:
    from app.engine.attributes import apply_mapping, map_fields

    df = gdf.drop(columns=[gdf.geometry.name])
    return dict(zip(gdf[id_col].astype(str), apply_mapping(df, map_fields(df)).to_dict("records")))


def validate_city(city_id: str, seed: int = VALIDATION_SEED, out_dir: Path | None = None) -> dict:
    from app.config import settings

    city = get_city(city_id)
    if not city:
        raise ValueError(f"Unknown city '{city_id}'")
    out_dir = Path(out_dir or settings.validation_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ward = out_dir / f"_ward_{city_id}"
    generate_ward(ward, seed=seed, origin_lonlat=(city["lon"], city["lat"]))

    cad = normalize(read_source(ward / "cadastral.geojson")[0]).gdf
    mun = normalize(read_source(ward / "municipal.geojson")[0]).gdf
    gt = json.loads((ward / "ground_truth.json").read_text())
    truth = {**gt["matches"], **gt["duplicates"]}

    matches = match_layers(cad, mun, "parcel_id", "Property_ID")
    primary = [m for m in matches if "duplicate_of" not in m.breakdown.evidence]
    correct = sum(truth.get(m.other_id) == m.base_id for m in primary)

    cad_attrs, mun_attrs = _attrs(cad, "parcel_id"), _attrs(mun, "Property_ID")
    area_flagged, owner_flagged = set(), set()
    for m in primary:
        fs = detect_conflicts(m.base_id, cad_attrs[m.base_id], {"municipal": m},
                              {"municipal": mun_attrs[m.other_id]})
        for f in fs:
            if f.conflict_type == "AREA_MISMATCH":
                area_flagged.add(m.base_id)
            if f.conflict_type == "OWNER_MISMATCH":
                owner_flagged.add(m.base_id)
    inj = {k: set(v) for k, v in gt["injected"].items()}

    report = {
        "city": city_id,
        "city_name": city["name"],
        "seed": seed,
        "label": "Synthetic validation dataset",
        "parcels": len(cad),
        "matched": len(primary),
        "match_precision": round(correct / len(primary), 4) if primary else None,
        "match_recall": round(correct / len(gt["matches"]), 4),
        "area_conflict_recall": round(len(area_flagged & inj["area_mismatch"]) / len(inj["area_mismatch"]), 4),
        "owner_conflict_recall": round(len(owner_flagged & inj["owner_different"]) / len(inj["owner_different"]), 4),
        "owner_false_positive_rate": round(len(owner_flagged & inj["owner_variant"]) / len(inj["owner_variant"]), 4),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / f"{city_id}.json").write_text(json.dumps(report, indent=1))
    return report


def load_validation(city_id: str) -> dict | None:
    from app.config import settings

    path = Path(settings.validation_dir) / f"{city_id}.json"
    return json.loads(path.read_text()) if path.is_file() else None


if __name__ == "__main__":
    for c in CITIES:
        if c["status"] == "validation":
            r = validate_city(c["id"])
            print(f"{c['name']}: precision {r['match_precision']:.1%}, recall {r['match_recall']:.1%}, "
                  f"area-conflict recall {r['area_conflict_recall']:.1%}")
