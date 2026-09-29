from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import analytics, cities, conflicts, datasets, harmonize, layers, parcels
from app.config import settings
from app.db import SessionLocal, get_session, init_db
from app.pipeline import recover_interrupted_runs


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
        with SessionLocal() as s:
            if n := recover_interrupted_runs(s):
                print(f"marked {n} interrupted harmonization run(s) as failed")
    except Exception as exc:  # DB may be down; /health reports it
        print(f"startup DB step failed: {exc}")
    yield


app = FastAPI(title="UrbanSync AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(harmonize.router)
for r in (parcels.router, conflicts.router, layers.router, analytics.router, cities.router):
    app.include_router(r)


@app.get("/health")
def health(session: Session = Depends(get_session)):
    body = {"status": "ok", "project_crs": settings.project_crs, "database": "ok", "postgis": None}
    try:
        body["postgis"] = session.execute(text("SELECT postgis_lib_version()")).scalar()
    except Exception:
        body["database"] = "error"
    return body
