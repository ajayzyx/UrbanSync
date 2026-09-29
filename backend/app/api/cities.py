import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cities import CITIES, DATASET_LABELS, get_city
from app.config import settings
from app.db import get_session
from app.models import CanonicalParcel, Conflict, Dataset, HarmonizationRun
from app.validate import load_validation

router = APIRouter(tags=["cities"])


def _demo_payload(session: Session) -> tuple[dict | None, dict | None]:
    """Live stats + test area for the demo city. Numbers are real or null — never invented."""
    cad = (session.query(Dataset).filter_by(source_type="cadastral")
           .filter(Dataset.record_count > 0).order_by(Dataset.version).first())
    if not cad:
        return None, None
    run = session.query(HarmonizationRun).filter_by(status="completed").order_by(HarmonizationRun.id.desc()).first()
    confs = [c for (c,) in session.query(CanonicalParcel.confidence_score) if c is not None]
    stats = {
        "parcels": cad.record_count,
        "matched": (run.summary or {}).get("matched") if run else None,
        "conflicts_total": (run.summary or {}).get("conflicts") if run else None,
        "conflicts_pending": session.query(Conflict).filter_by(status="Pending Review").count() if run else None,
        "avg_confidence": round(sum(confs) / len(confs), 4) if confs else None,
        "last_run_at": run.finished_at.isoformat() if run and run.finished_at else None,
    }
    test_area = None
    if cad.footprint is not None:
        g = func.ST_Transform(Dataset.footprint, 4326)
        geom, minx, miny, maxx, maxy = session.execute(
            select(func.ST_AsGeoJSON(g, 6), func.ST_XMin(g), func.ST_YMin(g), func.ST_XMax(g), func.ST_YMax(g))
            .where(Dataset.id == cad.id)).one()
        test_area = {"bbox": [round(v, 6) for v in (minx, miny, maxx, maxy)], "geometry": json.loads(geom)}
    return stats, test_area


def city_out(session: Session, c: dict) -> dict:
    out = {"id": c["id"], "name": c["name"], "state": c["state"], "coordinates": [c["lon"], c["lat"]],
           "status": c["status"], "dataset_type": None, "dataset_label": DATASET_LABELS.get(c["status"]),
           "stats": None, "test_area": None, "validation": None}
    if c["status"] == "demo" and c["id"] == settings.demo_city:
        out["dataset_type"] = "synthetic"
        out["stats"], out["test_area"] = _demo_payload(session)
    elif c["status"] == "validation":
        out["validation"] = load_validation(c["id"])
        out["dataset_type"] = "synthetic" if out["validation"] else None
    return out


@router.get("/cities")
def list_cities(session: Session = Depends(get_session)):
    return [city_out(session, c) for c in CITIES]


@router.get("/cities/{city_id}")
def get_city_detail(city_id: str, session: Session = Depends(get_session)):
    c = get_city(city_id)
    if not c:
        raise HTTPException(404, f"Unknown city '{city_id}'")
    return city_out(session, c)
