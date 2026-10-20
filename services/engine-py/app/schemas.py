from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DomainType(str, Enum):
    MARKETING = "marketing"
    PERSONAL = "personal"


class InferenceRequest(BaseModel):
    domain: DomainType
    task_type: str = Field(
        ...,
        description="Operation, e.g. campaign_analysis, copy_generation, daily_briefing, inbox_triage",
    )
    user_query: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    brand_voice_id: Optional[str] = None


class ActionItem(BaseModel):
    title: str
    priority: str = Field(..., pattern="^(high|medium|low)$")
    due_window: Optional[str] = None
    suggested_tool: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    summary: str
    structured_output: Dict[str, Any]
    recommended_actions: List[ActionItem] = Field(default_factory=list)
    grounding_sources: List[str] = Field(default_factory=list)


class CampaignRow(BaseModel):
    campaign: str = "default"
    channel: str = "unknown"
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0


class CampaignAnalysisRequest(BaseModel):
    rows: List[CampaignRow]
    brand_voice_id: Optional[str] = None


class CampaignAnalysisResponse(BaseModel):
    totals: Dict[str, Any]
    per_campaign: List[Dict[str, Any]]
    insights: List[str]
    best_campaign: Optional[str] = None
    worst_campaign: Optional[str] = None


class RagIngestRequest(BaseModel):
    collection: str = Field(..., pattern="^(brand|personal|domain4s)$")
    doc_id: str
    text: str


class RagRetrieveRequest(BaseModel):
    collection: str = Field(..., pattern="^(brand|personal|domain4s)$")
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class RagHit(BaseModel):
    doc_id: str
    score: float
    snippet: str


class RagRetrieveResponse(BaseModel):
    collection: str
    query: str
    hits: List[RagHit]
