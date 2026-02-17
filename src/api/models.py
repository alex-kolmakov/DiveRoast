from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class UploadResponse(BaseModel):
    session_id: str
    dive_count: int
    dive_numbers: list[str]
    message: str


# --- Dashboard models ---


class DiveFeature(BaseModel):
    dive_number: str
    avg_depth: float
    max_depth: float
    depth_variability: float
    avg_temp: float
    max_temp: float
    temp_variability: float
    avg_pressure: float
    max_pressure: float
    pressure_variability: float
    min_ndl: float
    sac_rate: float
    rating: float
    max_ascend_speed: float
    high_ascend_speed_count: float
    adverse_conditions: int


class DiveMetricPoint(BaseModel):
    dive_number: str
    value: float
    zone: str  # "safe", "warning", "danger"


class MetricRange(BaseModel):
    label: str
    unit: str
    min_val: float
    max_val: float
    avg_val: float
    safe_upper: float
    warning_upper: float
    zone: str  # "safe", "warning", "danger"
    per_dive: list[DiveMetricPoint]


class DanIssueNote(BaseModel):
    issue: str
    relevance: str
    search_url: str


class ProblematicDive(BaseModel):
    dive_number: str
    danger_score: float
    features: DiveFeature
    issues: list[str]
    dan_notes: list[DanIssueNote]


class AggregateStats(BaseModel):
    total_dives: int
    avg_max_depth: float
    avg_sac_rate: float
    avg_max_ascend_speed: float
    dives_with_adverse_conditions: int


class DashboardResponse(BaseModel):
    session_id: str
    aggregate_stats: AggregateStats
    metrics: list[MetricRange]
    all_dives: list[DiveFeature]
    top_problematic_dives: list[ProblematicDive]
