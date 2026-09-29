"""Harmonization run: orchestrates the engine and persists results. Each stage is committed as it runs,
so the UI polls real progress. Source features are read-only here."""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import geopandas as gpd
import shapely
from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db import SessionLocal
from app.engine.attributes import apply_mapping, map_fields
from app.engine.changes import detect_changes
from app.engine.conflicts import detect_conflicts
from app.engine.matching import Match, classify, explain, match_layers
from app.engine.ml import get_model, ml_probability
from app.engine.topology import validate_topology
from app.review import derive_status
from app.models import (SRID, AttributeMapping, CanonicalParcel, Conflict, Dataset, FeatureMatch,
                        HarmonizationRun, SourceFeature, TopologyIssue)

STAGES = [("ingest", "Ingest"), ("normalize", "Normalize CRS"), ("match", "Spatial match"),
          ("attributes", "Map attributes"), ("validate", "Validate topology"), ("resolve", "Detect conflicts"),
          ("harmonize", "Harmonize")]
STATUS_BY_CLASS = {"HIGH": "HARMONIZED", "REVIEW": "REVIEW", "CONFLICT": "CONFLICT"}
STATUS_RANK = {"HARMONIZED": 0, "REVIEW": 1, "CONFLICT": 2}
SOURCE_LABEL = {"municipal": "Municipal", "revenue": "Revenue"}
DERIVED = ["topology_issues", "conflicts", "feature_matches", "attribute_mappings", "canonical_parcels"]
STALE_AFTER = timedelta(minutes=10)
TOPOLOGY_ACTION = {"auto_safe": "Safe automatic correction applied to canonical geometry; source unchanged.",
                   "requires_review": "Correction suggested — requires review."}


class RunInProgress(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


RUN_LOCK_KEY = 26013  # pg advisory lock serialising run starts


def recover_interrupted_runs(session: Session) -> int:
    """Runs execute in-process, so any 'running' row at startup was interrupted by a restart."""
    rows = session.query(HarmonizationRun).filter_by(status="running").all()
    for r in rows:
        r.status, r.error, r.finished_at = "failed", "Interrupted by backend restart", _now()
    session.commit()
    return len(rows)


def start_run(session: Session) -> HarmonizationRun:
    session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": RUN_LOCK_KEY})  # released on commit/rollback
    for r in session.query(HarmonizationRun).filter_by(status="running"):
        started = r.started_at if r.started_at.tzinfo else r.started_at.replace(tzinfo=timezone.utc)
        if _now() - started > STALE_AFTER:
            r.status, r.error = "failed", "Run abandoned (stale)"
        else:
            session.rollback()
            raise RunInProgress("A harmonization run is already in progress")
    run = HarmonizationRun(status="running", summary={},
                           stages=[{"key": k, "label": lbl, "status": "pending", "started_at": None,
                                    "finished_at": None, "detail": None} for k, lbl in STAGES])
    session.add(run)
    session.commit()
    return run


def _set_stage(session: Session, run: HarmonizationRun, key: str, status: str, detail: str | None = None) -> None:
    stages = [dict(s) for s in run.stages]
    for s in stages:
        if s["key"] == key:
            s["status"] = status
            if status == "running":
                s["started_at"] = _now().isoformat()
            else:
                s["finished_at"] = _now().isoformat()
            if detail is not None:
                s["detail"] = detail
    run.stages = stages
    session.commit()


def _baselines(session: Session) -> tuple[dict[str, Dataset], dict[str, Dataset]]:
    """Latest baseline dataset per source type, and latest 'update' dataset (for change detection)."""
    base, upd = {}, {}
    for d in session.query(Dataset).order_by(Dataset.source_type, Dataset.version):
        target = upd if (d.metadata_ or {}).get("role") == "update" else base
        target[d.source_type] = d
    return base, upd


def _load(session: Session, ds: Dataset) -> gpd.GeoDataFrame:
    rows = session.query(SourceFeature.id, SourceFeature.record_id, SourceFeature.properties, SourceFeature.geom) \
        .filter(SourceFeature.dataset_id == ds.id).order_by(SourceFeature.id).all()
    recs = [{**(p or {}), "_sfid": sid, "_rid": rid} for sid, rid, p, _ in rows]
    return gpd.GeoDataFrame(recs, geometry=[to_shape(g) for *_, g in rows], crs=SRID)


def _attr_rows(gdf: gpd.GeoDataFrame) -> list[dict]:
    df = gdf.drop(columns=[gdf.geometry.name, "_sfid", "_rid"])
    return apply_mapping(df, map_fields(df)).to_dict("records")


def _poly(g):
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parts = [p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.unary_union(parts) if parts else g.buffer(0.05)


def run_harmonization(run_id: int, session_factory: sessionmaker = SessionLocal) -> None:
    session = session_factory()
    run = session.get(HarmonizationRun, run_id)
    current = None
    t0 = time.perf_counter()
    try:
        # 1. INGEST ---------------------------------------------------------------------------
        current = "ingest"
        _set_stage(session, run, current, "running")
        base, upd = _baselines(session)
        if "cadastral" not in base:
            raise ValueError("No cadastral dataset loaded — run the seed or upload a cadastral layer")
        vector = {k: d for k, d in base.items() if d.status != "registered"}
        registered = [d for d in base.values() if d.status == "registered"]
        g = {k: _load(session, d) for k, d in vector.items()}
        n_feat = sum(len(x) for x in g.values())
        _set_stage(session, run, current, "done",
                   f"{len(vector)} vector datasets · {n_feat:,} features · {len(registered)} registered metadata-only sources")

        # 2. NORMALIZE ------------------------------------------------------------------------
        current = "normalize"
        _set_stage(session, run, current, "running")
        crs_groups: dict[str, list[str]] = defaultdict(list)
        transforms = []
        for k, d in vector.items():
            crs_groups[d.source_crs or "unknown"].append(k)
            if d.source_crs and d.source_crs != settings.project_crs:
                t = {"dataset": k, "from": d.source_crs, "to": settings.project_crs}
                if t not in transforms:
                    transforms.append(t)
        invalid = sum(int((~x.geometry.is_valid).sum()) for x in g.values())
        parts = [f"{c} → {settings.project_crs} ({len(v)} datasets)" if c != settings.project_crs
                 else f"{c} native ({len(v)})" for c, v in sorted(crs_groups.items())]
        _set_stage(session, run, current, "done", f"{', '.join(parts)} · {invalid} invalid geometries flagged")

        # 3. MATCH ----------------------------------------------------------------------------
        current = "match"
        _set_stage(session, run, current, "running")
        cad = g["cadastral"]
        results: dict[str, list[Match]] = {}
        for src in ("municipal", "revenue"):
            if src in g:
                results[src] = match_layers(cad, g[src], "_rid", "_rid")
        primary = {s: {m.base_id: m for m in ms if "duplicate_of" not in m.breakdown.evidence} for s, ms in results.items()}
        dups: dict[str, list[Match]] = defaultdict(list)
        for m in results.get("municipal", []):
            if "duplicate_of" in m.breakdown.evidence:
                dups[m.base_id].append(m)
        model = get_model()  # advisory second opinion, trained on a different synthetic ward
        agree = []
        for m in results.get("municipal", []):
            m.breakdown.evidence["ml_probability"] = ml_probability(model, m.breakdown)
            if "duplicate_of" not in m.breakdown.evidence:
                agree.append((m.breakdown.evidence["ml_probability"] >= 0.5) == (m.breakdown.match_class != "CONFLICT"))
        mdetail = ", ".join(f"{len(primary[s])} {s}" for s in primary)
        _set_stage(session, run, current, "done",
                   f"{mdetail} matched · {sum(len(v) for v in dups.values())} duplicates found · "
                   f"ML check agrees on {sum(agree) / max(len(agree), 1):.1%}")

        # 4. MAP ATTRIBUTES -------------------------------------------------------------------
        current = "attributes"
        _set_stage(session, run, current, "running")
        mappings = []
        for k, x in g.items():
            df = x.drop(columns=[x.geometry.name, "_sfid", "_rid"])
            for fm in map_fields(df):
                mappings.append((vector[k].id, fm))
        attrs = {k: dict(zip(x["_rid"], _attr_rows(x))) for k, x in g.items() if k in ("cadastral", "municipal", "revenue")}
        mapped = [m for _, m in mappings if m.canonical_field]
        avg_map = sum(m.confidence for m in mapped) / len(mapped) if mapped else 0
        _set_stage(session, run, current, "done",
                   f"{len(mapped)} of {len(mappings)} fields mapped to canonical schema across {len(g)} datasets "
                   f"(avg confidence {avg_map:.0%})")

        # 5. VALIDATE TOPOLOGY ----------------------------------------------------------------
        current = "validate"
        _set_stage(session, run, current, "running")
        topo = validate_topology(cad, "_rid")
        tcount = Counter(f.issue_type for f in topo)
        _set_stage(session, run, current, "done",
                   " · ".join(f"{v} {k.lower().replace('_', ' ')}" for k, v in sorted(tcount.items())) or "No issues")

        # 6. DETECT CONFLICTS -----------------------------------------------------------------
        current = "resolve"
        _set_stage(session, run, current, "running")
        findings = {}
        for pid in cad["_rid"]:
            findings[pid] = detect_conflicts(
                pid, attrs["cadastral"][pid], {s: primary[s].get(pid) for s in primary},
                {s: attrs[s].get(primary[s][pid].other_id, {}) if pid in primary[s] else {} for s in primary},
                duplicates=dups.get(pid, []))
        invalid_ids = {f.parcel_id for f in topo if f.issue_type in ("SELF_INTERSECTION", "INVALID_GEOMETRY")}
        for pid in invalid_ids:  # area of an invalid ring is undefined; the TOPOLOGY conflict covers it
            findings[pid] = [f for f in findings[pid] if f.conflict_type != "AREA_MISMATCH"]
        topo_by_parcel: dict[str, list] = defaultdict(list)
        for f in topo:
            for pid in ([f.parcel_id] if f.parcel_id else []) + list(f.related):
                topo_by_parcel[pid].append(f)
        n_conf = sum(len(v) for v in findings.values()) + sum(len(v) for v in topo_by_parcel.values())
        n_par = len({p for p, v in findings.items() if v} | set(topo_by_parcel))
        _set_stage(session, run, current, "done", f"{n_conf} conflicts across {n_par} parcels queued for review")

        # 7. HARMONIZE (persist) --------------------------------------------------------------
        current = "harmonize"
        _set_stage(session, run, current, "running")
        # reviewer decisions are not derived data: capture them so they survive the rerun
        prev_decisions = {
            _conflict_key(c.parcel.parcel_id, c): (c.status, c.resolution, c.resolved_at)
            for c in session.query(Conflict).filter(Conflict.status != "Pending Review")}
        prev_resolved = {p.parcel_id: p.resolved_values for p in session.query(CanonicalParcel)
                         if p.resolved_values}
        for t in DERIVED:  # replace previous run's derived rows; run history is kept
            session.execute(text(f"DELETE FROM {t}"))
        for ds_id, fm in mappings:
            session.add(AttributeMapping(run_id=run.id, dataset_id=ds_id, source_field=fm.source_field,
                                         canonical_field=fm.canonical_field, confidence=fm.confidence, method=fm.method))

        sfid = {k: dict(zip(x["_rid"], x["_sfid"])) for k, x in g.items()}
        fixes = {f.parcel_id: f for f in topo if f.parcel_id and f.fix_status == "auto_safe" and f.suggested_fix}
        gnss_hits: dict[str, list[str]] = defaultdict(list)
        bld_hits: dict[str, list[str]] = defaultdict(list)
        valid_cad = [shapely.make_valid(x) if not x.is_valid else x for x in cad.geometry]
        tree = shapely.STRtree(valid_cad)
        cad_ids = list(cad["_rid"])
        if "gnss" in g:
            a, b = tree.query(list(g["gnss"].geometry), predicate="dwithin", distance=0.5)
            for i, j in zip(a, b):
                gnss_hits[cad_ids[j]].append(g["gnss"]["_rid"].iloc[i])
        if "buildings" in g:
            cents = [x.centroid for x in g["buildings"].geometry]
            a, b = tree.query(cents, predicate="within")
            for i, j in zip(a, b):
                bld_hits[cad_ids[j]].append(g["buildings"]["_rid"].iloc[i])

        parcels: dict[str, CanonicalParcel] = {}
        for idx, pid in enumerate(cad_ids):
            battrs = attrs["cadastral"][pid]
            ms = {s: primary[s].get(pid) for s in primary}
            geom = fixes[pid].suggested_fix if pid in fixes else cad.geometry.iloc[idx]
            topo_status = "SUGGESTED_FIX" if pid in fixes else ("ISSUE" if pid in topo_by_parcel else "VALID")
            finals = [m.breakdown.final for m in ms.values() if m]
            conf = round(sum(finals) / len(finals), 4) if finals else None
            if not finals:
                status = "UNMATCHED"
            else:
                status = max((STATUS_BY_CLASS[classify(m.breakdown.final)] for m in ms.values() if m),
                             key=STATUS_RANK.get)
                blocking = [f for f in findings[pid] if f.conflict_type != "MISSING_ATTRIBUTE"] or topo_by_parcel.get(pid)
                if blocking and status == "HARMONIZED":
                    status = "REVIEW"
            owner, land_use = battrs.get("owner_name"), battrs.get("land_use")
            for s, m in sorted(((s, m) for s, m in ms.items() if m), key=lambda t: -t[1].breakdown.final):
                oa = attrs[s].get(m.other_id, {})
                owner = owner or oa.get("owner_name")
                land_use = land_use or oa.get("land_use")
            prov = [{"source_type": "cadastral", "dataset_id": vector["cadastral"].id, "dataset_name": vector["cadastral"].name,
                     "source_feature_id": int(sfid["cadastral"][pid]), "record_id": pid}]
            for s, m in ms.items():
                if m:
                    prov.append({"source_type": s, "dataset_id": vector[s].id, "dataset_name": vector[s].name,
                                 "source_feature_id": int(sfid[s][m.other_id]), "record_id": m.other_id})
            for s, hits in (("gnss", gnss_hits.get(pid, [])), ("buildings", bld_hits.get(pid, []))):
                for rid in hits:
                    prov.append({"source_type": s, "dataset_id": vector[s].id, "dataset_name": vector[s].name,
                                 "source_feature_id": int(sfid[s][rid]), "record_id": rid})
            p = CanonicalParcel(run_id=run.id, parcel_id=pid, geom=from_shape(geom, srid=SRID),
                                area=round(shapely.make_valid(geom).area, 1), owner_name=owner, land_use=land_use,
                                source_count=1 + sum(1 for m in ms.values() if m) + (1 if gnss_hits.get(pid) else 0),
                                confidence_score=conf, match_status=status, topology_status=topo_status,
                                provenance=prov, resolved_values={}, building_count=len(bld_hits.get(pid, [])),
                                gnss_count=len(gnss_hits.get(pid, [])))
            parcels[pid] = p
            session.add(p)
        session.flush()

        for s, pm in primary.items():
            for pid, m in pm.items():
                _add_match(session, run.id, parcels[pid], s, m, sfid)
        for pid, ms in dups.items():
            for m in ms:
                _add_match(session, run.id, parcels[pid], "municipal", m, sfid)
        new_conflicts: list[Conflict] = []
        for pid, fs in findings.items():
            for f in fs:
                new_conflicts.append(Conflict(run_id=run.id, canonical_parcel_id=parcels[pid].id, conflict_type=f.conflict_type,
                                     source_a=f.source_a, source_b=f.source_b, field=f.field, observed=f.observed,
                                     confidence=f.confidence, explanation=f.explanation,
                                     recommended_action=f.recommended_action))
        for f in topo:
            owner_p = parcels.get(f.parcel_id) if f.parcel_id else None
            session.add(TopologyIssue(run_id=run.id, canonical_parcel_id=owner_p.id if owner_p else None,
                                      issue_type=f.issue_type, geom=from_shape(_poly(f.location), srid=SRID),
                                      detail=f.detail, fix_status=f.fix_status,
                                      suggested_fix=from_shape(f.suggested_fix, srid=SRID) if f.suggested_fix else None))
        for pid, fs in topo_by_parcel.items():
            for f in fs:
                new_conflicts.append(Conflict(run_id=run.id, canonical_parcel_id=parcels[pid].id, conflict_type="TOPOLOGY",
                                     source_a="cadastral", source_b="cadastral", field=None,
                                     observed={"a": f.issue_type, "b": ", ".join([x for x in [f.parcel_id, *f.related] if x and x != pid]) or None,
                                               "delta": f"{f.location.area:.1f} m²"},
                                     confidence=0.95, explanation=f.detail,
                                     recommended_action=TOPOLOGY_ACTION[f.fix_status]))
        session.add_all(new_conflicts)
        session.flush()

        # re-apply reviewer decisions from the previous run
        pid_by_id = {p.id: pid for pid, p in parcels.items()}
        touched: set[str] = set()
        for c in new_conflicts:
            prev = prev_decisions.get(_conflict_key(pid_by_id[c.canonical_parcel_id], c))
            if prev:
                c.status, c.resolution, c.resolved_at = prev
                touched.add(pid_by_id[c.canonical_parcel_id])
        for pid, rv in prev_resolved.items():
            if pid in parcels:
                parcels[pid].resolved_values = rv
                for fld, entry in rv.items():
                    if fld in ("area", "owner_name", "land_use"):
                        setattr(parcels[pid], fld, entry.get("value"))
                touched.add(pid)
        session.flush()
        for pid in touched:
            session.refresh(parcels[pid])
            parcels[pid].match_status = derive_status(parcels[pid])
        carried = len(touched)

        changes = {"NEW": 0, "REMOVED": 0, "MODIFIED": 0, "UNCHANGED": 0}
        if "municipal" in upd and "municipal" in g:
            v2 = _load(session, upd["municipal"])
            for c in detect_changes(g["municipal"].drop(columns=["_sfid"]), v2.drop(columns=["_sfid"]), "_rid"):
                changes[c.change] += 1
        for d in vector.values():
            d.status, d.last_processed = "processed", _now()
        for d in upd.values():
            d.last_processed = _now()

        statuses = Counter(p.match_status for p in parcels.values())
        confs = [p.confidence_score for p in parcels.values() if p.confidence_score is not None]
        n_conflicts = sum(len(v) for v in findings.values()) + sum(len(v) for v in topo_by_parcel.values())
        run.summary = {
            "datasets": len(vector) + len(registered) + len(upd), "features": n_feat, "parcels": len(parcels),
            "matched": len(primary.get("municipal", {})), "revenue_matched": len(primary.get("revenue", {})),
            "high": statuses.get("HARMONIZED", 0), "review": statuses.get("REVIEW", 0),
            "conflict_class": statuses.get("CONFLICT", 0), "unmatched": statuses.get("UNMATCHED", 0),
            "conflicts": n_conflicts, "topology_issues": len(topo),
            "avg_confidence": round(sum(confs) / len(confs), 4) if confs else None,
            "crs_transforms": transforms, "changes": changes,
            "duration_s": round(time.perf_counter() - t0, 2),
        }
        session.flush()
        avg = run.summary["avg_confidence"]
        _set_stage(session, run, current, "done",
                   f"{len(parcels):,} canonical parcels · avg confidence {f'{avg:.1%}' if avg is not None else 'n/a'} · "
                   f"provenance kept for every record" + (f" · {carried} reviewer decisions carried forward" if carried else ""))
        run.status, run.finished_at = "completed", _now()
        run.summary = {**run.summary, "duration_s": round(time.perf_counter() - t0, 2)}
        session.commit()
    except Exception as exc:  # record failure truthfully
        session.rollback()
        run = session.get(HarmonizationRun, run_id)
        if current:
            _set_stage(session, run, current, "failed", str(exc)[:300])
        run.status, run.error, run.finished_at = "failed", str(exc)[:1000], _now()
        session.commit()
        raise
    finally:
        session.close()


def _add_match(session: Session, run_id: int, parcel: CanonicalParcel, src: str, m: Match, sfid: dict) -> None:
    b = m.breakdown
    session.add(FeatureMatch(
        run_id=run_id, source_feature_id=int(sfid[src][m.other_id]), target_feature_id=int(sfid["cadastral"][m.base_id]),
        canonical_parcel_id=parcel.id, source_type=src, geometry_score=b.geometry, centroid_score=b.centroid,
        area_score=b.area, shape_score=b.shape, attribute_score=b.attribute, temporal_score=b.temporal,
        final_confidence=b.final, match_class=b.match_class, evidence=b.evidence,
        explanation=explain(b, m.base_id, m.other_id, SOURCE_LABEL.get(src, src.title()))))


def _conflict_key(parcel_id: str, c: Conflict) -> tuple:
    o = c.observed or {}
    return (parcel_id, c.conflict_type, c.source_b, c.field, str(o.get("a")), str(o.get("b")))
