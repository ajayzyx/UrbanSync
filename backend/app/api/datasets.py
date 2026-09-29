import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.ingest.readers import ALLOWED_EXTENSIONS, IngestError, sanitize
from app.ingest.store import SOURCE_TYPES, ingest_file
from app.models import Dataset
from app.schemas import DatasetOut

router = APIRouter(tags=["datasets"])


def to_out(d: Dataset) -> DatasetOut:
    return DatasetOut.model_validate({**{k: getattr(d, k) for k in DatasetOut.model_fields if hasattr(d, k)},
                                      "metadata": d.metadata_ or {}, "target_crs": settings.project_crs})


@router.get("/datasets", response_model=list[DatasetOut])
def list_datasets(session: Session = Depends(get_session)):
    return [to_out(d) for d in session.query(Dataset).order_by(Dataset.id)]


@router.post("/datasets/upload", response_model=DatasetOut, status_code=201)
def upload_dataset(file: UploadFile = File(...), source_type: str = Form(...), crs: str | None = Form(None),
                   name: str | None = Form(None), session: Session = Depends(get_session)):
    fname = sanitize(Path(file.filename or "upload").name)
    ext = Path(fname).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(422, f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    if source_type not in SOURCE_TYPES:
        raise HTTPException(422, f"Unknown source_type '{source_type}'")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=settings.upload_dir) as tmp:
        dest = Path(tmp) / fname
        with open(dest, "wb") as fh:
            shutil.copyfileobj(file.file, fh, length=1024 * 1024)
        if dest.stat().st_size > settings.max_upload_bytes:
            raise HTTPException(422, "File exceeds 20 MB limit")
        try:
            latest = session.query(Dataset).filter_by(source_type=source_type).order_by(Dataset.version.desc()).first()
            ds = ingest_file(session, dest, source_type, name or fname, crs_hint=crs or None,
                             version=(latest.version + 1) if latest else 1, file_name=fname)
            session.commit()
        except IngestError as exc:
            session.rollback()
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:  # any parser/transform failure is a bad file, not a server error
            session.rollback()
            raise HTTPException(422, f"Could not ingest file: {str(exc)[:200]}") from exc
    return to_out(ds)
