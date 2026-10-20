"""Tool registry (Registry pattern).

Every capability the brain can use is a named Tool with an explicit contract:
what it does, whether it mutates the outside world, and whether a human must
approve it first. Mutating tools are never executed by the brain. They are
returned as pending approvals for the TypeScript layer to gate.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from ..domain4s.campaign_brief import build_campaign_brief
from ..domain4s.content_calendar import build_calendar
from ..domain4s.guardrails import check_draft
from ..domain4s.lead_scoring import score_leads
from ..domain4s.retention import build_retention_segments
from ..pipelines.marketing_analytics import analyze_campaign_metrics
from ..pipelines.personal import build_daily_briefing
from ..pipelines.rag import KB


GENERIC_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": True,
}


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[Dict[str, Any]], Any]
    mutating: bool = False
    requires_approval: bool = False
    tags: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=lambda: dict(GENERIC_INPUT_SCHEMA))

    def mcp_descriptor(self) -> Dict[str, Any]:
        """MCP tools/list shape: name, description, inputSchema."""
        return {"name": self.name, "description": self.description, "inputSchema": self.input_schema}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool registration: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def mcp_list(self) -> List[Dict[str, Any]]:
        return [t.mcp_descriptor() for t in self._tools.values()]

    def list(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "mutating": t.mutating,
                "requires_approval": t.requires_approval,
                "tags": t.tags,
            }
            for t in self._tools.values()
        ]


def _rag_retrieve(args: Dict[str, Any]) -> Any:
    collection = args.get("collection", "domain4s")
    hits = KB.get(collection).search(args.get("query", ""), top_k=int(args.get("top_k", 3)))
    return [{"doc_id": d, "score": s, "snippet": snip} for d, s, snip in hits]


def build_default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(Tool(
        name="analytics.campaign_performance",
        description="Pandas campaign analytics: CTR, CPC, CPA, ROAS, best and worst campaign, insights",
        handler=lambda a: analyze_campaign_metrics(a.get("metrics", [])),
        tags=["marketing", "analytics"],
    ))
    reg.register(Tool(
        name="domain4s.score_leads",
        description="Explainable prospect lead scoring for dealers and workshops",
        handler=lambda a: score_leads(a.get("leads", [])),
        tags=["marketing", "domain4s", "crm"],
    ))
    reg.register(Tool(
        name="domain4s.retention_segments",
        description="Maintenance due, lapsed, detractor and promoter segments from service records",
        handler=lambda a: {"segments": build_retention_segments(a.get("records", []))},
        tags=["marketing", "domain4s", "retention"],
    ))
    reg.register(Tool(
        name="domain4s.content_calendar",
        description="Monthly content calendar from the 4S PLUS content pillars",
        handler=lambda a: {"slots": build_calendar(int(a.get("weeks", 4)), int(a.get("posts_per_week", 3)), a.get("audience", "prospecting"))},
        tags=["marketing", "domain4s", "content"],
    ))
    reg.register(Tool(
        name="domain4s.campaign_brief",
        description="Build a campaign plan from brief answers: audiences, pillars, cadence, KPIs, missing fields",
        handler=lambda a: build_campaign_brief(a.get("brief", a)),
        tags=["marketing", "domain4s", "planning"],
        input_schema={
            "type": "object",
            "properties": {
                "product_focus": {"type": "string"},
                "audience_type": {"type": "string", "enum": ["prospecting", "dealer_marketing"]},
                "monthly_goal": {"type": "string", "enum": ["demos", "appointments", "awareness"]},
                "channels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["product_focus", "audience_type", "monthly_goal"],
        },
    ))
    reg.register(Tool(
        name="guardrails.check_draft",
        description="Prohibited claims and unverified percentage check on any draft",
        handler=lambda a: check_draft(a.get("text", ""), a.get("allowed_numbers", [])),
        tags=["safety", "content"],
    ))
    reg.register(Tool(
        name="rag.retrieve",
        description="Retrieve grounding documents from brand, personal, or domain4s knowledge",
        handler=_rag_retrieve,
        tags=["rag", "grounding"],
    ))
    reg.register(Tool(
        name="personal.daily_briefing",
        description="Daily briefing synthesis from calendar events and triaged email",
        handler=lambda a: build_daily_briefing(a.get("calendar_events", []), a.get("emails", [])),
        tags=["personal"],
    ))
    # Mutating tools exist in the registry so plans can reference them, but the
    # brain refuses to execute them. Approval and execution live in TypeScript.
    reg.register(Tool(
        name="social.schedule_draft",
        description="Schedule an approved draft for publishing",
        handler=lambda a: {"status": "never executed by the brain"},
        mutating=True, requires_approval=True, tags=["marketing", "publish"],
    ))
    reg.register(Tool(
        name="crm.create_followup_task",
        description="Create a follow up task in the CRM for a hot lead",
        handler=lambda a: {"status": "never executed by the brain"},
        mutating=True, requires_approval=True, tags=["crm"],
    ))
    reg.register(Tool(
        name="campaign.prepare_outreach",
        description="Prepare an outreach batch for a retention segment",
        handler=lambda a: {"status": "never executed by the brain"},
        mutating=True, requires_approval=True, tags=["marketing", "retention"],
    ))
    reg.register(Tool(
        name="calendar.create_focus_block",
        description="Create a focus block on the user calendar",
        handler=lambda a: {"status": "never executed by the brain"},
        mutating=True, requires_approval=True, tags=["personal"],
    ))
    return reg
