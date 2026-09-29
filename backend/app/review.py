"""Parcel status after human review — shared by the resolve API and the pipeline's rerun carry-forward."""

from __future__ import annotations

from app.engine.matching import classify
from app.models import CanonicalParcel

BLOCKING = {"AREA_MISMATCH", "OWNER_MISMATCH", "SPATIAL_MISMATCH", "DUPLICATE", "BOUNDARY_OVERLAP", "TOPOLOGY"}
CONFIRMING = {"Resolved", "Accepted"}
STATUS_BY_CLASS = {"HIGH": "HARMONIZED", "REVIEW": "REVIEW", "CONFLICT": "CONFLICT"}
RANK = {"HARMONIZED": 0, "REVIEW": 1, "CONFLICT": 2}


def derive_status(parcel: CanonicalParcel) -> str:
    """Status never beats the match score, except that a reviewer may confirm a REVIEW-class parcel.

    - no cross-source match                          -> UNMATCHED
    - pending blocking conflict                      -> at least REVIEW
    - REVIEW class + a blocking conflict confirmed   -> HARMONIZED (reviewer-confirmed)
    - CONFLICT class is never promoted; "Ignored" never confirms.
    """
    primary = [m for m in parcel.matches if "duplicate_of" not in (m.evidence or {})]
    if not primary:
        return "UNMATCHED"
    status = max((STATUS_BY_CLASS[classify(m.final_confidence)] for m in primary), key=RANK.get)
    blocking = [c for c in parcel.conflicts if c.conflict_type in BLOCKING]
    if any(c.status == "Pending Review" for c in blocking):
        return "CONFLICT" if status == "CONFLICT" else "REVIEW"
    if status == "REVIEW" and any(c.status in CONFIRMING for c in blocking):
        return "HARMONIZED"
    return status
