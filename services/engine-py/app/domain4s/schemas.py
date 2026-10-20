from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProspectLead(BaseModel):
    company: str
    business_type: str = Field(
        ..., description="dealer | workshop | parts_trader | fleet | other"
    )
    branches: int = 1
    monthly_jobs_or_sales: int = 0
    current_system: str = Field(default="excel", description="excel | paper | other_erp | none")
    signals: List[str] = Field(
        default_factory=list,
        description="Engagement signals: demo_requested, pricing_page, replied, referral, event_meeting, website_visit",
    )
    days_since_last_touch: int = 999


class ScoredLead(BaseModel):
    company: str
    score: int
    tier: str = Field(..., pattern="^(hot|warm|cold)$")
    reasons: List[str]
    next_action: str


class LeadScoreRequest(BaseModel):
    leads: List[ProspectLead]


class LeadScoreResponse(BaseModel):
    scored: List[ScoredLead]
    hot_count: int


class VehicleServiceRecord(BaseModel):
    customer: str
    chassis: str
    months_since_last_service: float = 0.0
    km_since_last_service: int = 0
    service_interval_months: int = 6
    service_interval_km: int = 10000
    last_survey_score: Optional[int] = Field(default=None, ge=0, le=10)
    open_jobcard: bool = False


class RetentionRequest(BaseModel):
    records: List[VehicleServiceRecord]


class RetentionSegment(BaseModel):
    segment: str
    customers: List[Dict[str, Any]]
    playbook: str
    channel: str
    human_first: bool = False


class RetentionResponse(BaseModel):
    segments: List[RetentionSegment]


class ContentCalendarRequest(BaseModel):
    weeks: int = Field(default=4, ge=1, le=8)
    posts_per_week: int = Field(default=3, ge=1, le=7)
    audience: str = Field(default="prospecting", pattern="^(prospecting|dealer_marketing)$")


class CalendarSlot(BaseModel):
    week: int
    pillar: str
    module_focus: str
    format: str
    hook: str
    cta: str


class ContentCalendarResponse(BaseModel):
    audience: str
    slots: List[CalendarSlot]


class GuardrailCheckRequest(BaseModel):
    text: str
    allowed_numbers: List[str] = Field(
        default_factory=list,
        description="Numbers backed by a real source, e.g. verified product facts. Any other percentage in the text is flagged.",
    )


class GuardrailCheckResponse(BaseModel):
    ok: bool
    violations: List[str]
