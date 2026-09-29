import json
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.common import clean
from app.api.harmonize import run_out
from app.db import get_session
from app.models import (AttributeMapping, CanonicalParcel, Conflict, Dataset, FeatureMatch, HarmonizationRun,
                        SourceFeature, TopologyIssue)

router = APIRouter(tags=["analytics"])
STATUSES = ["HARMONIZED", "REVIEW", "CONFLICT", "UNMATCHED"]


def _evaluation(session: Session, parcels: dict[int, str]) -> dict | None:
    cad = session.query(Dataset).filter_by(source_type="cadastral").order_by(Dataset.version).first()
    path = Path((cad.metadata_ or {}).get("ground_truth_path", "")) if cad else None
    if not path or not path.is_file() or not parcels:
        return None
    gt = json.loads(path.read_text())
    truth = {**gt["matches"], **gt.get("duplicates", {})}
    primary = [m for m in session.query(FeatureMatch).filter_by(source_type="municipal")
               if "duplicate_of" not in (m.evidence or {})]
    preds = [(m.source_feature.record_id, parcels[m.canonical_parcel_id]) for m in primary]
    correct = sum(truth.get(o) == p for o, p in preds)
    ml = [(m, truth.get(m.source_feature.record_id) == parcels[m.canonical_parcel_id])
          for m in primary if (m.evidence or {}).get("ml_probability") is not None]
    ml_pos = [ok for m, ok in ml if m.evidence["ml_probability"] >= 0.5]
    ml_agree = [(m.evidence["ml_probability"] >= 0.5) == (m.match_class != "CONFLICT") for m, _ in ml]
    area = {c.parcel.parcel_id for c in session.query(Conflict).filter_by(conflict_type="AREA_MISMATCH", source_b="municipal")}
    owner = {c.parcel.parcel_id for c in session.query(Conflict).filter_by(conflict_type="OWNER_MISMATCH")}
    inj = {k: set(v) for k, v in gt["injected"].items()}
    return {
        "label": "Evaluated on synthetic ground truth",
        "match_precision": round(correct / len(preds), 4) if preds else None,
        "match_recall": round(correct / len(gt["matches"]), 4),
        "area_conflict_recall": round(len(area & inj["area_mismatch"]) / len(inj["area_mismatch"]), 4),
        "owner_conflict_recall": round(len(owner & inj["owner_different"]) / len(inj["owner_different"]), 4),
        "owner_false_positive_rate": round(len(owner & inj["owner_variant"]) / len(inj["owner_variant"]), 4),
        "ml_match_precision": round(sum(ml_pos) / len(ml_pos), 4) if ml_pos else None,
        "ml_baseline_agreement": round(sum(ml_agree) / len(ml_agree), 4) if ml_agree else None,
    }


@router.get("/analytics")
def analytics(session: Session = Depends(get_session)):
    run = session.query(HarmonizationRun).filter_by(status="completed").order_by(HarmonizationRun.id.desc()).first()
    latest = session.query(HarmonizationRun).order_by(HarmonizationRun.id.desc()).first()
    parcels = session.query(CanonicalParcel.id, CanonicalParcel.parcel_id, CanonicalParcel.match_status,
                            CanonicalParcel.confidence_score).all()
    conflicts = session.query(Conflict.conflict_type, Conflict.status).all()
    topo = Counter(t for (t,) in session.query(TopologyIssue.issue_type))
    datasets = session.query(Dataset).all()
    status = Counter(s for _, _, s, _ in parcels)
    confs = [c for *_, c in parcels if c is not None]
    pending = sum(1 for _, s in conflicts if s == "Pending Review")
    summary = run.summary if run else {}

    hist = [{"bin": f"{i / 10:.1f}–{(i + 1) / 10:.1f}", "count": 0} for i in range(10)]
    for c in confs:
        hist[min(int(c * 10), 9)]["count"] += 1
    if len(confs) < len(parcels):
        hist.append({"bin": "n/a", "count": len(parcels) - len(confs)})

    baseline = [d for d in datasets if d.status != "registered" and (d.metadata_ or {}).get("role") != "update"]
    owner_fields = {m.source_field for m in session.query(AttributeMapping).filter_by(canonical_field="owner_name")}
    invalid_before = session.query(SourceFeature).join(Dataset).filter(Dataset.source_type == "cadastral",
                                                                       SourceFeature.geom_valid.is_(False)).count()
    invalid_pending = sum(1 for c in session.query(Conflict).filter_by(conflict_type="TOPOLOGY", status="Pending Review")
                          if (c.observed or {}).get("a") in ("SELF_INTERSECTION", "INVALID_GEOMETRY"))
    quality = [
        {"metric": "Distinct CRS", "before": len({d.source_crs for d in baseline}), "after": 1 if parcels else None},
        {"metric": "Owner-name field schemas", "before": len(owner_fields) or None, "after": 1 if parcels else None},
        {"metric": "Parcels linked across sources", "before": 0, "after": summary.get("matched")},
        {"metric": "Discrepancies surfaced for review", "before": 0, "after": len(conflicts)},
        {"metric": "Invalid geometries unresolved", "before": invalid_before, "after": invalid_pending if parcels else None},
    ]
    id_map = {i: pid for i, pid, *_ in parcels}
    return clean({
        "kpis": {
            "datasets": len(datasets), "parcels": len(parcels), "matched": summary.get("matched", 0),
            "high": status.get("HARMONIZED", 0), "review": status.get("REVIEW", 0),
            "conflict_class": status.get("CONFLICT", 0), "unmatched": status.get("UNMATCHED", 0),
            "conflicts_total": len(conflicts), "conflicts_pending": pending,
            "conflicts_resolved": sum(1 for _, s in conflicts if s != "Pending Review"),
            "topology_issues": sum(topo.values()),
            "avg_confidence": round(sum(confs) / len(confs), 4) if confs else None,
            "last_run_at": run.finished_at.isoformat() if run and run.finished_at else None,
        },
        "match_distribution": [{"class": s, "count": status.get(s, 0)} for s in STATUSES],
        "confidence_histogram": hist,
        "conflict_breakdown": [{"type": t, "count": n} for t, n in Counter(t for t, _ in conflicts).most_common()],
        "topology_stats": [{"type": t, "count": n} for t, n in topo.most_common()],
        "quality_before_after": quality,
        "evaluation": _evaluation(session, id_map),
        "run": run_out(latest).model_dump(mode="json") if latest else None,
    })
