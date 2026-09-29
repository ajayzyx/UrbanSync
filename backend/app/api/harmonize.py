from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_session
from app.models import AttributeMapping, HarmonizationRun
from app.pipeline import RunInProgress, run_harmonization, start_run

router = APIRouter(tags=["harmonization"])


class RunOut(BaseModel):
    id: int
    status: str
    stages: list[dict]
    summary: dict
    started_at: datetime
    finished_at: datetime | None
    error: str | None


def run_out(r: HarmonizationRun) -> RunOut:
    return RunOut(id=r.id, status=r.status, stages=r.stages or [], summary=r.summary or {}, started_at=r.started_at,
                  finished_at=r.finished_at, error=r.error)


def _safe_run(run_id: int, factory: sessionmaker) -> None:
    try:
        run_harmonization(run_id, factory)
    except Exception as exc:  # already recorded on the run row
        print(f"harmonization run {run_id} failed: {exc}")


@router.post("/harmonize", status_code=202)
def harmonize(background: BackgroundTasks, session: Session = Depends(get_session)):
    try:
        run = start_run(session)
    except RunInProgress as exc:
        raise HTTPException(409, str(exc)) from exc
    background.add_task(_safe_run, run.id, sessionmaker(bind=session.get_bind(), expire_on_commit=False))
    return {"run_id": run.id}


@router.get("/harmonization/latest", response_model=RunOut)
def latest_run(session: Session = Depends(get_session)):
    r = session.query(HarmonizationRun).order_by(HarmonizationRun.id.desc()).first()
    if not r:
        raise HTTPException(404, "No harmonization run yet")
    return run_out(r)


@router.get("/harmonization/{run_id}", response_model=RunOut)
def get_run(run_id: int, session: Session = Depends(get_session)):
    r = session.get(HarmonizationRun, run_id)
    if not r:
        raise HTTPException(404, "Run not found")
    return run_out(r)


@router.get("/harmonization/{run_id}/mappings")
def get_mappings(run_id: int, session: Session = Depends(get_session)):
    rows = session.query(AttributeMapping).filter_by(run_id=run_id).order_by(AttributeMapping.id).all()
    return [{"dataset": m.dataset.name, "source_type": m.dataset.source_type, "source_field": m.source_field,
             "canonical_field": m.canonical_field, "confidence": m.confidence, "method": m.method} for m in rows]
