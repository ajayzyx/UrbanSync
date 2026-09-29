"""Turn matched multi-source records into reviewable conflict findings."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.matching import Match

SOURCE_LABEL = {"cadastral": "Cadastral", "municipal": "Municipal", "revenue": "Revenue", "gnss": "GNSS"}
AREA_PCT = 5.0
OWNER_MIN_SIM = 0.6
IOU_MIN = 0.75
ACTIONS = {
    "AREA_MISMATCH": "Verify with field survey; prefer GNSS-backed area.",
    "OWNER_MISMATCH": "Manual review required — confirm with revenue record.",
    "MISSING_ATTRIBUTE": "Backfill from highest-confidence source (suggested).",
    "SPATIAL_MISMATCH": "Manual review required.",
    "DUPLICATE": "Retain one record; mark the other as duplicate.",
}


@dataclass
class ConflictFinding:
    parcel_id: str
    conflict_type: str
    source_a: str
    source_b: str
    observed: dict
    confidence: float
    explanation: str
    recommended_action: str
    field: str | None = None
    other_id: str | None = None


def _finding(pid, ctype, src, observed, conf, text, field=None, other_id=None) -> ConflictFinding:
    return ConflictFinding(pid, ctype, "cadastral", src, observed, round(conf, 3), text, ACTIONS[ctype], field, other_id)


def detect_conflicts(parcel_id: str, base_attrs: dict, matches: dict[str, Match | None],
                     other_attrs: dict[str, dict], duplicates: list[Match] | tuple = ()) -> list[ConflictFinding]:
    out: list[ConflictFinding] = []
    for src, match in matches.items():
        if match is None:
            continue
        ev, label = match.breakdown.evidence, SOURCE_LABEL.get(src, src.title())
        attrs = other_attrs.get(src, {})

        pct = ev.get("area_diff_pct")
        if pct is not None and pct > AREA_PCT:
            a, b = ev.get("area_a_sqm"), ev.get("area_b_sqm")
            out.append(_finding(parcel_id, "AREA_MISMATCH", src, {"a": a, "b": b, "delta": f"{pct:.1f}%"},
                                max(0.6, min(1.0, pct / 15)),
                                f"Area differs by {pct:.1f}% ({a:.0f} m² cadastral vs {b:.0f} m² {label.lower()}).",
                                "area", match.other_id))

        sim = ev.get("name_similarity")
        if sim is not None and sim < OWNER_MIN_SIM:
            out.append(_finding(parcel_id, "OWNER_MISMATCH", src,
                                {"a": base_attrs.get("owner_name"), "b": attrs.get("owner_name"), "delta": f"{sim:.0%} similar"},
                                1 - sim,
                                f"Owner names disagree ({sim:.0%} similarity) between cadastral and {label.lower()} records.",
                                "owner_name", match.other_id))

        for fld in ("owner_name", "land_use"):
            if attrs.get(fld) is None and base_attrs.get(fld) is not None:
                out.append(_finding(parcel_id, "MISSING_ATTRIBUTE", src,
                                    {"a": base_attrs.get(fld), "b": None, "delta": "missing"}, 0.9,
                                    f"{label} record has no {fld.replace('_', ' ')}; cadastral value is available.",
                                    fld, match.other_id))

        iou, inside = ev.get("iou"), ev.get("point_in_polygon")
        if iou is not None and iou < IOU_MIN:
            d = ev.get("centroid_distance_m") or 0
            out.append(_finding(parcel_id, "SPATIAL_MISMATCH", src, {"a": "cadastral boundary", "b": f"{label.lower()} boundary",
                                                                      "delta": f"IoU {iou:.0%}"}, 0.9,
                                f"{label} and cadastral geometries overlap by only {iou:.0%}; centroids are {d:.1f} m apart.",
                                None, match.other_id))
        elif inside is False:
            out.append(_finding(parcel_id, "SPATIAL_MISMATCH", src, {"a": "cadastral boundary", "b": f"{label.lower()} location",
                                                                      "delta": "outside"}, 0.9,
                                f"{label} record location lies outside the cadastral parcel boundary.",
                                None, match.other_id))

    for dup in duplicates:
        first = dup.breakdown.evidence.get("duplicate_of")
        out.append(ConflictFinding(parcel_id, "DUPLICATE", "municipal", "municipal",
                                   {"a": first, "b": dup.other_id, "delta": f"IoU {dup.breakdown.evidence.get('iou', 0):.0%}"},
                                   0.9, f"Municipal records {first} and {dup.other_id} describe the same parcel.",
                                   ACTIONS["DUPLICATE"], None, dup.other_id))
    return out
