"""Generate (if missing) and load the deterministic demo datasets. Idempotent."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.ingest.store import ingest_file, register_source
from app.models import Dataset
from app.synthetic import generate_ward

DEMO_FILES = [
    ("cadastral.geojson", "cadastral", "Synthetic cadastral parcels - demo survey schema", 1),
    ("municipal.geojson", "municipal", "Synthetic municipal GIS parcels", 1),
    ("municipal_v2.geojson", "municipal", "Synthetic municipal GIS parcels - update", 2),
    ("revenue.csv", "revenue", "Synthetic revenue records - Khasra schema", 1),
    ("buildings.geojson", "buildings", "Synthetic building footprints", 1),
    ("gnss.csv", "gnss", "Synthetic GNSS ground-truth points", 1),
    ("roads.geojson", "roads", "Synthetic road centrelines", 1),
]

DERIVED_TABLES = ["topology_issues", "conflicts", "feature_matches", "attribute_mappings", "canonical_parcels",
                  "harmonization_runs", "source_features", "datasets"]


def seed_demo(session: Session, data_dir: Path | None = None) -> list[Dataset]:
    data_dir = Path(data_dir or settings.data_dir)
    if not (data_dir / "ground_truth.json").exists():
        generate_ward(data_dir)
    session.execute(text(f"TRUNCATE {', '.join(DERIVED_TABLES)} RESTART IDENTITY CASCADE"))
    session.expunge_all()  # ids restart; drop stale identities
    out = [ingest_file(session, data_dir / f, st, name, version=v) for f, st, name, v in DEMO_FILES]
    for d in out:
        if d.source_type == "cadastral":
            d.metadata_ = {**d.metadata_, "ground_truth_path": str(data_dir / "ground_truth.json")}
        if d.source_type == "municipal" and d.version == 2:
            d.metadata_ = {**d.metadata_, "role": "update"}  # incoming version, used for change detection
    for entry in json.loads((data_dir / "registered_sources.json").read_text()):
        out.append(register_source(session, entry))
    for d in out:
        d.metadata_ = {**d.metadata_, "city": settings.demo_city, "data_origin": "synthetic"}
    session.commit()
    _ensure_validation_reports()
    return out


def _ensure_validation_reports() -> None:
    """Second-city engine validation (spec v2 §35); built once, cached on disk."""
    from app.cities import CITIES
    from app.validate import validate_city

    for c in CITIES:
        if c["status"] == "validation" and not (settings.validation_dir / f"{c['id']}.json").is_file():
            r = validate_city(c["id"])
            print(f"validation[{c['id']}]: precision {r['match_precision']:.1%}")


if __name__ == "__main__":
    from app.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as s:
        for d in seed_demo(s):
            print(f"{d.source_type:10} v{d.version} {d.record_count:5} {d.source_crs}  {d.name}")
