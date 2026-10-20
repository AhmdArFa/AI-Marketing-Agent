from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BrainRunRequest(BaseModel):
    session_id: str = Field(default="default", max_length=128)
    goal: str = Field(..., min_length=3, max_length=2000)
    context: Dict[str, Any] = Field(default_factory=dict)
    explicit_domain: Optional[str] = Field(default=None, pattern="^(marketing|personal)$")


class BrainPlanStep(BaseModel):
    order: int
    tool: str
    kind: str
    note: str


class BrainRunResponse(BaseModel):
    session_id: str
    domain: str
    skill_id: Optional[str] = None
    plan_reason: str
    plan_steps: List[BrainPlanStep]
    results: Dict[str, Any]
    pending_approvals: List[Dict[str, Any]]
    blocked_approvals: List[Dict[str, Any]] = Field(default_factory=list)
    shield: Optional[Dict[str, Any]] = None
    draft_evaluation: Optional[Dict[str, Any]] = None
    executed_mutations: List[Any]
    grounding: List[Dict[str, Any]]
    guardrail: Optional[Dict[str, Any]] = None
    summary: str
    session_summary: Optional[str] = None
    context_report: Optional[Dict[str, Any]] = None
    trace: Optional[Dict[str, Any]] = None
    memory_insights: Dict[str, Any]
