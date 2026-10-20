from fastapi import FastAPI, HTTPException

from .brain import Brain
from .brain.schemas import BrainRunRequest, BrainRunResponse
from .domain4s.campaign_brief import build_campaign_brief
from .domain4s.content_calendar import build_calendar
from .domain4s.guardrails import check_draft
from .domain4s.lead_scoring import score_leads
from .domain4s.retention import build_retention_segments
from .domain4s.schemas import (
    ContentCalendarRequest,
    ContentCalendarResponse,
    GuardrailCheckRequest,
    GuardrailCheckResponse,
    LeadScoreRequest,
    LeadScoreResponse,
    RetentionRequest,
    RetentionResponse,
)
from .models.llm_client import LLMClient
from .security import SecurityMiddleware, auth_enabled
from .pipelines.marketing_analytics import analyze_campaign_metrics
from .pipelines.personal import build_daily_briefing, triage_emails
from .pipelines.rag import KB
from .schemas import (
    ActionItem,
    CampaignAnalysisRequest,
    CampaignAnalysisResponse,
    DomainType,
    InferenceRequest,
    InferenceResponse,
    RagHit,
    RagIngestRequest,
    RagRetrieveRequest,
    RagRetrieveResponse,
)

app = FastAPI(title="AI Marketing Agent: Data, Model and Brain Layer", version="0.2.0")
app.add_middleware(SecurityMiddleware)
llm = LLMClient()
brain = Brain()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "layer": "python-data-model-brain",
        "llm_provider": llm.provider,
        "auth_enabled": auth_enabled(),
        "skills_loaded": len(brain.planner.skills),
        "tools_registered": len(brain.registry.list()),
    }


@app.post("/v1/brain/run", response_model=BrainRunResponse)
def brain_run(req: BrainRunRequest) -> BrainRunResponse:
    try:
        result = brain.run(req.session_id, req.goal, req.context, req.explicit_domain)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return BrainRunResponse(**result)


@app.get("/v1/brain/skills")
def brain_skills() -> dict:
    return {
        "skills": [
            {"id": s.id, "name": s.name, "domain": s.domain, "description": s.description}
            for s in brain.planner.skills
        ]
    }


@app.get("/v1/brain/tools")
def brain_tools(format: str = "native") -> dict:
    if format == "mcp":
        return {"tools": brain.registry.mcp_list()}
    return {"tools": brain.registry.list()}


@app.get("/metrics")
def metrics() -> dict:
    from .security import metrics_snapshot

    return metrics_snapshot()


@app.post("/v1/analytics/campaign", response_model=CampaignAnalysisResponse)
def campaign_analysis(req: CampaignAnalysisRequest) -> CampaignAnalysisResponse:
    result = analyze_campaign_metrics([r.model_dump() for r in req.rows])
    return CampaignAnalysisResponse(**result)


@app.post("/v1/rag/ingest")
def rag_ingest(req: RagIngestRequest) -> dict:
    KB.get(req.collection).add_document(req.doc_id, req.text)
    return {"status": "ingested", "collection": req.collection, "doc_id": req.doc_id}


@app.post("/v1/rag/retrieve", response_model=RagRetrieveResponse)
def rag_retrieve(req: RagRetrieveRequest) -> RagRetrieveResponse:
    hits = KB.get(req.collection).search(req.query, top_k=req.top_k)
    return RagRetrieveResponse(
        collection=req.collection,
        query=req.query,
        hits=[RagHit(doc_id=d, score=s, snippet=snip) for d, s, snip in hits],
    )


@app.post("/v1/domain4s/lead-score", response_model=LeadScoreResponse)
def domain_lead_score(req: LeadScoreRequest) -> LeadScoreResponse:
    return LeadScoreResponse(**score_leads([lead.model_dump() for lead in req.leads]))


@app.post("/v1/domain4s/retention", response_model=RetentionResponse)
def domain_retention(req: RetentionRequest) -> RetentionResponse:
    segments = build_retention_segments([r.model_dump() for r in req.records])
    return RetentionResponse(segments=segments)


@app.post("/v1/domain4s/content-calendar", response_model=ContentCalendarResponse)
def domain_calendar(req: ContentCalendarRequest) -> ContentCalendarResponse:
    slots = build_calendar(req.weeks, req.posts_per_week, req.audience)
    return ContentCalendarResponse(audience=req.audience, slots=slots)


@app.post("/v1/domain4s/campaign-brief")
def domain_campaign_brief(payload: dict) -> dict:
    return build_campaign_brief(payload)


@app.post("/v1/domain4s/guardrails/check", response_model=GuardrailCheckResponse)
def domain_guardrails(req: GuardrailCheckRequest) -> GuardrailCheckResponse:
    return GuardrailCheckResponse(**check_draft(req.text, req.allowed_numbers))


@app.post("/v1/engine/execute", response_model=InferenceResponse)
def execute(req: InferenceRequest) -> InferenceResponse:
    if req.domain == DomainType.MARKETING:
        metrics = analyze_campaign_metrics(req.context_data.get("metrics", []))
        hits = KB.brand.search(req.user_query, top_k=3)
        sources = [f"vector_store://brand/{doc_id}" for doc_id, _, _ in hits]
        draft = llm.draft_copy(req.user_query, sources, req.brand_voice_id)
        actions = [
            ActionItem(
                title="Review campaign draft before scheduling",
                priority="high",
                suggested_tool="social.scheduleDraft",
                payload={"topic": req.user_query, "draft": draft},
            )
        ]
        return InferenceResponse(
            summary=f"Marketing pipeline complete for task {req.task_type}.",
            structured_output={"computed_metrics": metrics, "draft_copy": draft},
            recommended_actions=actions,
            grounding_sources=sources or ["vector_store://brand/voice-v1"],
        )

    if req.domain == DomainType.PERSONAL:
        events = req.context_data.get("calendar_events", [])
        emails = req.context_data.get("emails", [])
        if req.task_type == "inbox_triage":
            structured = {"triaged_emails": triage_emails(emails)}
            summary = f"Triaged {len(emails)} email(s)."
        else:
            structured = {"briefing": build_daily_briefing(events, emails)}
            summary = structured["briefing"]["headline"]
        hits = KB.personal.search(req.user_query, top_k=3)
        return InferenceResponse(
            summary=summary,
            structured_output=structured,
            recommended_actions=[
                ActionItem(
                    title="Block focus time on calendar",
                    priority="medium",
                    due_window="Today 09:30",
                    suggested_tool="calendar.createFocusBlock",
                    payload={"start": "09:30", "duration_minutes": 120},
                )
            ],
            grounding_sources=[f"personal_kb://{doc_id}" for doc_id, _, _ in hits],
        )

    raise HTTPException(status_code=400, detail="Unsupported domain")
