from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.common import conflict_out, parcel_detail, source_values
from app.db import get_session
from app.models import CanonicalParcel, Conflict, HarmonizationRun
from app.review import derive_status

router = APIRouter(tags=["conflicts"])

ALIASES = {
    "area": ["AREA_MISMATCH"],
    "boundary": ["SPATIAL_MISMATCH", "BOUNDARY_OVERLAP"],
    "attribute": ["OWNER_MISMATCH", "MISSING_ATTRIBUTE"],
    "duplicate": ["DUPLICATE"],
    "topology": ["TOPOLOGY"],
}
VALUE_FIELDS = {"area", "owner_name", "land_use"}


class ResolveIn(BaseModel):
    status: Literal["Accepted", "Resolved", "Ignored"]
    chosen_source: Literal["cadastral", "municipal", "revenue"] | None = None
    field: str | None = None
    note: str | None = None


@router.get("/conflicts")
def list_conflicts(type: str | None = None, status: str | None = None, limit: int = 500,
                   session: Session = Depends(get_session)):
    qry = session.query(Conflict).join(CanonicalParcel)
    if type and type.lower() != "all":
        qry = qry.filter(Conflict.conflict_type.in_(ALIASES.get(type.lower(), [type.upper()])))
    if status:
        qry = qry.filter(Conflict.status == status)
    rows = qry.order_by(Conflict.confidence.desc(), Conflict.id).limit(max(1, min(limit, 2000))).all()
    return [conflict_out(session, c) for c in rows]


def _get(session: Session, conflict_id: int) -> Conflict:
    c = session.get(Conflict, conflict_id)
    if not c:
        raise HTTPException(404, "Conflict not found")
    return c


@router.get("/conflicts/{conflict_id}")
def get_conflict(conflict_id: int, session: Session = Depends(get_session)):
    return conflict_out(session, _get(session, conflict_id), with_values=True)


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(conflict_id: int, body: ResolveIn, session: Session = Depends(get_session)):
    """Record a reviewer decision. Writes only to the canonical parcel; source records are never modified."""
    if session.query(HarmonizationRun).filter_by(status="running").count():
        raise HTTPException(409, "A harmonization run is in progress — try again when it completes")
    c = _get(session, conflict_id)
    parcel = c.parcel
    field = c.field or body.field  # a value conflict always resolves its own field
    now = datetime.now(timezone.utc)
    resolution = {"status": body.status, "chosen_source": body.chosen_source, "field": field, "note": body.note,
                  "resolved_by": "reviewer"}
    if body.status == "Resolved" and field in VALUE_FIELDS:
        if not body.chosen_source:
            raise HTTPException(422, "chosen_source is required to resolve a value conflict")
        values = source_values(session, parcel).get(body.chosen_source)
        if values is None:
            raise HTTPException(422, f"Parcel has no linked {body.chosen_source} record")
        value = values.get(field)
        if value is None:
            raise HTTPException(422, f"{body.chosen_source} record has no value for {field}; choose another source")
        rv = dict(parcel.resolved_values or {})
        rv[field] = {"value": value, "source": body.chosen_source, "resolved_by": "reviewer",
                     "resolved_at": now.isoformat(), "note": body.note, "conflict_id": c.id}
        parcel.resolved_values = rv
        flag_modified(parcel, "resolved_values")
        setattr(parcel, field, value)
        resolution["value"] = value
    c.status, c.resolution, c.resolved_at = body.status, resolution, now
    session.flush()
    session.refresh(parcel)
    parcel.match_status = derive_status(parcel)
    parcel.last_updated = now
    session.commit()
    session.refresh(parcel)
    return parcel_detail(session, parcel)
