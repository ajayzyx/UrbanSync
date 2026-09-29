from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.config import settings


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    source_type: str
    version: int
    file_name: str | None
    record_count: int
    source_crs: str | None
    target_crs: str = settings.project_crs
    status: str
    last_processed: datetime | None
    fields: list[str]
    metadata: dict[str, Any] = {}
