from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.api.common import parcel_detail, parcel_summary
from app.db import get_session
from app.models import CanonicalParcel

router = APIRouter(tags=["parcels"])


@router.get("/parcels")
def list_parcels(q: str | None = None, status: str | None = None, limit: int = 50,
                 session: Session = Depends(get_session)):
    g = func.ST_Transform(CanonicalParcel.geom, 4326)
    stmt = select(CanonicalParcel, func.ST_XMin(g), func.ST_YMin(g), func.ST_XMax(g), func.ST_YMax(g))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(CanonicalParcel.parcel_id.ilike(like), CanonicalParcel.owner_name.ilike(like),
                              cast(CanonicalParcel.provenance, String).ilike(like)))
    if status:
        stmt = stmt.where(CanonicalParcel.match_status == status.upper())
    stmt = stmt.order_by(CanonicalParcel.parcel_id).limit(max(1, min(limit, 1000)))
    return [parcel_summary(session, p, [round(v, 7) for v in box]) for p, *box in session.execute(stmt)]


@router.get("/parcels/{parcel_id}")
def get_parcel(parcel_id: str, session: Session = Depends(get_session)):
    p = session.query(CanonicalParcel).filter_by(parcel_id=parcel_id).first()
    if not p:
        raise HTTPException(404, f"Parcel {parcel_id} not found")
    return parcel_detail(session, p)
