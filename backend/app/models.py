from __future__ import annotations

from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

SRID = 32643


def now() -> datetime:
    return datetime.now(timezone.utc)


def geom_col(nullable: bool = False):
    return mapped_column(Geometry(srid=SRID, spatial_index=True), nullable=nullable)


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    file_name: Mapped[str | None] = mapped_column(String(200))
    source_crs: Mapped[str | None] = mapped_column(String(40))
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ingested")
    fields: Mapped[list] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    footprint = geom_col(nullable=True)
    last_processed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SourceFeature(Base):
    __tablename__ = "source_features"
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    record_id: Mapped[str] = mapped_column(String(80), index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    geom = geom_col()
    geom_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    dataset: Mapped[Dataset] = relationship()


class HarmonizationRun(Base):
    __tablename__ = "harmonization_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    stages: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class AttributeMapping(Base):
    __tablename__ = "attribute_mappings"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harmonization_runs.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    source_field: Mapped[str] = mapped_column(String(120))
    canonical_field: Mapped[str | None] = mapped_column(String(60))
    confidence: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(20))
    dataset: Mapped[Dataset] = relationship()


class CanonicalParcel(Base):
    __tablename__ = "canonical_parcels"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harmonization_runs.id", ondelete="CASCADE"), index=True)
    parcel_id: Mapped[str] = mapped_column(String(40), index=True, unique=True)  # one canonical row per parcel
    geom = geom_col()
    area: Mapped[float | None] = mapped_column(Float)
    owner_name: Mapped[str | None] = mapped_column(String(200))
    land_use: Mapped[str | None] = mapped_column(String(60))
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    match_status: Mapped[str] = mapped_column(String(20), index=True)
    topology_status: Mapped[str] = mapped_column(String(20), default="VALID")
    provenance: Mapped[list] = mapped_column(JSON, default=list)
    resolved_values: Mapped[dict] = mapped_column(JSON, default=dict)
    building_count: Mapped[int] = mapped_column(Integer, default=0)
    gnss_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    conflicts: Mapped[list[Conflict]] = relationship(back_populates="parcel")
    matches: Mapped[list[FeatureMatch]] = relationship(back_populates="parcel")
    topology: Mapped[list[TopologyIssue]] = relationship(back_populates="parcel")


class FeatureMatch(Base):
    __tablename__ = "feature_matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harmonization_runs.id", ondelete="CASCADE"), index=True)
    source_feature_id: Mapped[int] = mapped_column(ForeignKey("source_features.id", ondelete="CASCADE"))
    target_feature_id: Mapped[int] = mapped_column(ForeignKey("source_features.id", ondelete="CASCADE"))
    canonical_parcel_id: Mapped[int] = mapped_column(ForeignKey("canonical_parcels.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(40))
    geometry_score: Mapped[float | None] = mapped_column(Float)
    centroid_score: Mapped[float | None] = mapped_column(Float)
    area_score: Mapped[float | None] = mapped_column(Float)
    shape_score: Mapped[float | None] = mapped_column(Float)
    attribute_score: Mapped[float | None] = mapped_column(Float)
    temporal_score: Mapped[float | None] = mapped_column(Float)
    final_confidence: Mapped[float] = mapped_column(Float)
    match_class: Mapped[str] = mapped_column(String(20))
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[str] = mapped_column(Text)
    parcel: Mapped[CanonicalParcel] = relationship(back_populates="matches")
    source_feature: Mapped[SourceFeature] = relationship(foreign_keys=[source_feature_id])


class Conflict(Base):
    __tablename__ = "conflicts"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harmonization_runs.id", ondelete="CASCADE"), index=True)
    canonical_parcel_id: Mapped[int] = mapped_column(ForeignKey("canonical_parcels.id", ondelete="CASCADE"), index=True)
    conflict_type: Mapped[str] = mapped_column(String(30), index=True)
    source_a: Mapped[str] = mapped_column(String(40))
    source_b: Mapped[str] = mapped_column(String(40))
    field: Mapped[str | None] = mapped_column(String(40))
    observed: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="Pending Review", index=True)
    resolution: Mapped[dict | None] = mapped_column(JSON)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parcel: Mapped[CanonicalParcel] = relationship(back_populates="conflicts")


class TopologyIssue(Base):
    __tablename__ = "topology_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("harmonization_runs.id", ondelete="CASCADE"), index=True)
    canonical_parcel_id: Mapped[int | None] = mapped_column(ForeignKey("canonical_parcels.id", ondelete="CASCADE"))
    issue_type: Mapped[str] = mapped_column(String(30))
    geom = geom_col()
    detail: Mapped[str] = mapped_column(Text)
    suggested_fix = geom_col(nullable=True)
    fix_status: Mapped[str] = mapped_column(String(20))
    parcel: Mapped[CanonicalParcel | None] = relationship(back_populates="topology")
