"""Tool registry (Registry pattern).

Every capability the brain can use is a named Tool with an explicit contract:
what it does, whether it mutates the outside world, and whether a human must
approve it first. Mutating tools are never executed by the brain. They are
returned as pending approvals for the TypeScript layer to gate.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

MAX_RESULT_CHARS = 20_000

from ..domain4s.campaign_brief import build_campaign_brief
from ..generation.copywriter import generate_campaign
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
    # Permission scope, least privilege by construction: read and compute run
    # freely inside the brain; write and external can only ever be proposals.
    scope: str = "compute"

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

    def execute(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Safe execution contract (Tool Design): never raises into the loop.

        Returns {ok, data|error, duration_ms, truncated}. Oversized results
        are summarized, tool exceptions become structured errors the harness
        can retry or degrade on.
        """
        tool = self.get(name)
        started = time.perf_counter()
        try:
            data = tool.handler(args)
            duration = round((time.perf_counter() - started) * 1000, 2)
            truncated = False
            if len(repr(data)) > MAX_RESULT_CHARS:
                truncated = True
                if isinstance(data, list):
                    data = {"truncated_list": True, "count": len(data), "sample": data[:3]}
                elif isinstance(data, dict):
                    data = {"truncated_dict": True, "keys": list(data)[:20]}
                else:
                    data = {"truncated_value": True, "preview": repr(data)[:500]}
            return {"ok": True, "data": data, "duration_ms": duration, "truncated": truncated}
        except Exception as exc:
            duration = round((time.perf_counter() - started) * 1000, 2)
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "duration_ms": duration}

    def mcp_list(self) -> List[Dict[str, Any]]:
        return [t.mcp_descriptor() for t in self._tools.values()]

    def list(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "mutating": t.mutating,
                "requires_approval": t.requires_approval,
                "scope": t.scope,
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
        name="generation.campaign_package",
        description="Generate real marketing posts (text, channel variants, image brief) for a named company and domain",
        handler=lambda a: generate_campaign(
            company_name=a.get("company_name", "Vo Technology"),
            product_name=a.get("product_name", "4S PLUS"),
            domain=a.get("domain", "automotive_erp"),
            audience=a.get("audience", "prospecting"),
            language=a.get("language", "en"),
            count=int(a.get("count", 3)),
        ),
        tags=["marketing", "generation"],
        input_schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string"},
                "product_name": {"type": "string"},
                "domain": {"type": "string"},
                "audience": {"type": "string", "enum": ["prospecting", "dealer_marketing"]},
                "language": {"type": "string", "enum": ["en", "ar"]},
                "count": {"type": "integer"},
            },
            "required": ["company_name"],
        },
    ))
    reg.register(Tool(
        name="publishing.publish",
        description="Push an approved post package to a channel (file export, webhook, Meta). Executed only by the orchestrator after a human approval, through POST /v1/publish; the brain can only propose it",
        handler=lambda a: {"status": "requires_orchestrator_execution",
                           "detail": "Mutations execute only via /v1/publish after human approval"},
        mutating=True,
        requires_approval=True,
        tags=["publishing", "external"],
        scope="external",
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
