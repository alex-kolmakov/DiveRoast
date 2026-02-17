import logging
from urllib.parse import quote_plus

from fastapi import APIRouter, HTTPException

from src.analysis.feature_engineering import extract_features
from src.api.dependencies import get_session
from src.api.models import (
    AggregateStats,
    DanIssueNote,
    DashboardResponse,
    DiveFeature,
    DiveMetricPoint,
    MetricRange,
    ProblematicDive,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Safety thresholds: (label, unit, safe_upper, warning_upper)
THRESHOLDS = {
    "max_depth": ("Max Depth", "m", 18.0, 30.0),
    "max_ascend_speed": ("Max Ascent Speed", "m/min", 9.0, 10.0),
    "min_ndl": ("Min NDL", "min", None, None),  # inverted: lower is worse
    "sac_rate": ("SAC Rate", "L/min", 15.0, 20.0),
    "avg_temp": ("Avg Temperature", "\u00b0C", None, None),  # informational
}

# NDL thresholds are inverted: >10 safe, 5-10 warning, <5 danger
NDL_SAFE_LOWER = 10.0
NDL_WARNING_LOWER = 5.0

# Temperature: cold warning <10
TEMP_COLD_WARNING = 10.0

DAN_SEARCH_BASE = "https://dan.org/?s="

# Hardcoded relevance notes per issue type
ISSUE_RELEVANCE = {
    "rapid ascent": (
        "Rapid ascents are a leading cause of decompression sickness (DCS). "
        "DAN reports show that even brief uncontrolled ascents can cause arterial gas embolism, "
        "especially when combined with other risk factors like dehydration or repetitive dives."
    ),
    "low NDL": (
        "Pushing close to or exceeding no-decompression limits dramatically increases DCS risk. "
        "DAN incident data shows many cases where divers who 'just barely made it' developed "
        "symptoms hours later, often requiring hyperbaric treatment."
    ),
    "high air consumption": (
        "High air consumption reduces your safety margin and can lead to out-of-air emergencies. "
        "DAN has documented numerous incidents where poor gas management forced dangerous "
        "buddy-breathing ascents or emergency swimming ascents from depth."
    ),
    "deep dive": (
        "Deep recreational dives beyond 30m increase nitrogen narcosis risk and reduce bottom time. "
        "DAN reports highlight incidents where impaired judgment at depth led to poor decisions, "
        "missed decompression obligations, and fatal outcomes."
    ),
    "adverse conditions": (
        "Dives in poor conditions (low visibility, strong currents, cold water) compound other risks. "
        "DAN case studies show that adverse conditions are a multiplier — a minor issue at the surface "
        "becomes a life-threatening emergency when conditions deteriorate."
    ),
}

ISSUE_SEARCH_TERMS = {
    "rapid ascent": "rapid ascent decompression sickness",
    "low NDL": "decompression limit exceeded",
    "high air consumption": "out of air emergency",
    "deep dive": "deep dive narcosis incident",
    "adverse conditions": "adverse conditions diving emergency",
}


def _classify_zone(value: float, safe_upper: float, warning_upper: float) -> str:
    if value <= safe_upper:
        return "safe"
    if value <= warning_upper:
        return "warning"
    return "danger"


def _classify_ndl_zone(value: float) -> str:
    if value >= NDL_SAFE_LOWER:
        return "safe"
    if value >= NDL_WARNING_LOWER:
        return "warning"
    return "danger"


def _classify_temp_zone(value: float) -> str:
    if value >= TEMP_COLD_WARNING:
        return "safe"
    return "warning"


def _classify_single_value(
    col: str, value: float, safe_up: float | None, warn_up: float | None
) -> str:
    """Classify a single value into a zone for a given metric column."""
    if col == "min_ndl":
        return _classify_ndl_zone(value)
    if col == "avg_temp":
        return _classify_temp_zone(value)
    assert safe_up is not None and warn_up is not None
    return _classify_zone(value, safe_up, warn_up)


def _build_metrics(features_df) -> list[MetricRange]:
    metrics = []
    for col, (label, unit, safe_up, warn_up) in THRESHOLDS.items():
        if col not in features_df.columns:
            continue
        series = features_df[col]
        min_val = float(series.min())
        max_val = float(series.max())
        avg_val = float(series.mean())

        # Build per-dive values, sorted by value
        per_dive = []
        for _, row in features_df.iterrows():
            val = float(row[col])
            pt_zone = _classify_single_value(col, val, safe_up, warn_up)
            per_dive.append(
                DiveMetricPoint(
                    dive_number=str(row["dive_number"]),
                    value=round(val, 2),
                    zone=pt_zone,
                )
            )
        per_dive.sort(key=lambda p: p.value)

        if col == "min_ndl":
            zone = _classify_ndl_zone(min_val)
            metrics.append(
                MetricRange(
                    label=label,
                    unit=unit,
                    min_val=min_val,
                    max_val=max_val,
                    avg_val=avg_val,
                    safe_upper=NDL_SAFE_LOWER,
                    warning_upper=NDL_WARNING_LOWER,
                    zone=zone,
                    per_dive=per_dive,
                )
            )
        elif col == "avg_temp":
            zone = _classify_temp_zone(min_val)
            metrics.append(
                MetricRange(
                    label=label,
                    unit=unit,
                    min_val=min_val,
                    max_val=max_val,
                    avg_val=avg_val,
                    safe_upper=TEMP_COLD_WARNING,
                    warning_upper=0.0,
                    zone=zone,
                    per_dive=per_dive,
                )
            )
        else:
            assert safe_up is not None and warn_up is not None
            zone = _classify_zone(max_val, safe_up, warn_up)
            metrics.append(
                MetricRange(
                    label=label,
                    unit=unit,
                    min_val=min_val,
                    max_val=max_val,
                    avg_val=avg_val,
                    safe_upper=safe_up,
                    warning_upper=warn_up,
                    zone=zone,
                    per_dive=per_dive,
                )
            )
    return metrics


def _compute_danger_score(row) -> float:
    score = 0.0
    # NDL: lower is worse (weight 3)
    if row.get("min_ndl", 999) < NDL_WARNING_LOWER:
        score += 3.0 * 2
    elif row.get("min_ndl", 999) < NDL_SAFE_LOWER:
        score += 3.0

    # Ascent speed (weight 2)
    ascent = row.get("max_ascend_speed", 0)
    if ascent > 10:
        score += 2.0 * 2
    elif ascent > 9:
        score += 2.0

    # SAC rate (weight 1)
    sac = row.get("sac_rate", 0)
    if sac > 20:
        score += 1.0 * 2
    elif sac > 15:
        score += 1.0

    # Depth (weight 1)
    depth = row.get("max_depth", 0)
    if depth > 30:
        score += 1.0 * 2
    elif depth > 18:
        score += 1.0

    # Adverse conditions (weight 5)
    if row.get("adverse_conditions", 0):
        score += 5.0

    return score


def _identify_issues(row) -> list[str]:
    issues = []
    if row.get("max_ascend_speed", 0) > 9:
        issues.append("rapid ascent")
    if row.get("min_ndl", 999) < NDL_SAFE_LOWER:
        issues.append("low NDL")
    if row.get("sac_rate", 0) > 15:
        issues.append("high air consumption")
    if row.get("max_depth", 0) > 30:
        issues.append("deep dive")
    if row.get("adverse_conditions", 0):
        issues.append("adverse conditions")
    return issues


@router.get("/api/dashboard/{session_id}", response_model=DashboardResponse)
async def get_dashboard(session_id: str):
    """Compute dashboard data from session dive data. Pure computation, no LLM calls."""
    agent = get_session(session_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if agent.dive_data is None:
        raise HTTPException(status_code=400, detail="No dive data in session")

    features_df = extract_features(agent.dive_data)

    # Build per-dive features list
    all_dives = []
    for _, row in features_df.iterrows():
        all_dives.append(
            DiveFeature(
                dive_number=str(row["dive_number"]),
                avg_depth=round(float(row["avg_depth"]), 2),
                max_depth=round(float(row["max_depth"]), 2),
                depth_variability=round(float(row["depth_variability"]), 2),
                avg_temp=round(float(row["avg_temp"]), 2),
                max_temp=round(float(row["max_temp"]), 2),
                temp_variability=round(float(row["temp_variability"]), 2),
                avg_pressure=round(float(row["avg_pressure"]), 2),
                max_pressure=round(float(row["max_pressure"]), 2),
                pressure_variability=round(float(row["pressure_variability"]), 2),
                min_ndl=round(float(row["min_ndl"]), 2),
                sac_rate=round(float(row["sac_rate"]), 2),
                rating=round(float(row["rating"]), 1),
                max_ascend_speed=round(float(row["max_ascend_speed"]), 2),
                high_ascend_speed_count=round(float(row["high_ascend_speed_count"]), 0),
                adverse_conditions=int(row["adverse_conditions"]),
            )
        )

    # Compute metrics with per-dive values
    metrics = _build_metrics(features_df)

    # Compute aggregate stats
    aggregate_stats = AggregateStats(
        total_dives=len(features_df),
        avg_max_depth=round(float(features_df["max_depth"].mean()), 2),
        avg_sac_rate=round(float(features_df["sac_rate"].mean()), 2),
        avg_max_ascend_speed=round(float(features_df["max_ascend_speed"].mean()), 2),
        dives_with_adverse_conditions=int(features_df["adverse_conditions"].sum()),
    )

    # Compute danger scores and find top 3
    danger_scores = []
    for _, row in features_df.iterrows():
        row_dict = row.to_dict()
        score = _compute_danger_score(row_dict)
        danger_scores.append((str(row["dive_number"]), score, row_dict))

    danger_scores.sort(key=lambda x: x[1], reverse=True)
    top_3 = danger_scores[:3]

    # Build problematic dives with DAN issue notes + search links
    top_problematic_dives = []
    for dive_num, score, row_dict in top_3:
        if score == 0:
            continue
        issues = _identify_issues(row_dict)
        dan_notes = []
        for issue in issues:
            relevance = ISSUE_RELEVANCE.get(
                issue, f"This dive was flagged for: {issue}"
            )
            search_term = ISSUE_SEARCH_TERMS.get(issue, issue)
            search_url = f"{DAN_SEARCH_BASE}{quote_plus(search_term)}"
            dan_notes.append(
                DanIssueNote(
                    issue=issue,
                    relevance=relevance,
                    search_url=search_url,
                )
            )

        feature = next(d for d in all_dives if d.dive_number == dive_num)
        top_problematic_dives.append(
            ProblematicDive(
                dive_number=dive_num,
                danger_score=round(score, 2),
                features=feature,
                issues=issues,
                dan_notes=dan_notes,
            )
        )

    return DashboardResponse(
        session_id=session_id,
        aggregate_stats=aggregate_stats,
        metrics=metrics,
        all_dives=all_dives,
        top_problematic_dives=top_problematic_dives,
    )
