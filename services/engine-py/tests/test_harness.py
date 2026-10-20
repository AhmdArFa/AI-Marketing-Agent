from fastapi.testclient import TestClient

from app.brain import Brain
from app.brain.harness import recent_traces
from app.brain.tools_registry import Tool, ToolRegistry
from app.main import app

client = TestClient(app)
LEADS = [
    {
        "company": "Delta Motors", "business_type": "dealer", "branches": 3,
        "monthly_jobs_or_sales": 240, "current_system": "excel",
        "signals": ["demo_requested"], "days_since_last_touch": 2,
    }
]


def test_trace_and_context_report_present():
    brain = Brain()
    out = brain.run("trace-test", "Score my dealer leads and follow up", {"leads": LEADS})
    trace = out["trace"]
    assert trace["run_id"] and trace["iterations"] == 1
    assert trace["status"] == "ok"
    span_names = [s["name"] for s in trace["spans"]]
    assert "shield.scan" in span_names and "planner.plan" in span_names
    assert any(n.startswith("tool:") for n in span_names)
    assert out["context_report"]["budget_chars"] == 12000
    assert out["context_report"]["used_chars"] <= 12000 + 2000
    assert "1 turn(s) this session" in out["session_summary"]
    assert recent_traces(5)


def test_approval_proposals_are_enriched():
    brain = Brain()
    out = brain.run(
        "enrich-test", "Generate posts for this company",
        {"company_name": "Vo Technology", "count": 1},
    )
    proposal = out["pending_approvals"][0]
    assert proposal["tool"] == "publishing.publish"
    assert proposal["risk"] == "high"
    assert proposal["scope"] == "external"
    assert proposal["expires_in_minutes"] == 30
    assert proposal["preview"]


def test_tool_failure_retries_then_degrades_never_crashes():
    brain = Brain()
    tool = brain.registry.get("domain4s.score_leads")
    original = tool.handler
    calls = {"n": 0}

    def flaky(args):
        calls["n"] += 1
        raise RuntimeError("boom")

    tool.handler = flaky
    try:
        out = brain.run("fail-test", "Score my dealer leads", {"leads": LEADS})
    finally:
        tool.handler = original
    assert calls["n"] == 2  # first attempt + exactly one retry
    assert out["trace"]["status"] == "degraded"
    assert out["results"]["domain4s.score_leads"]["degraded"] is True
    assert "boom" in out["results"]["domain4s.score_leads"]["error"]


def test_registry_execute_contract():
    reg = ToolRegistry()
    reg.register(Tool(name="t.ok", description="ok", handler=lambda a: {"v": 1}))
    reg.register(Tool(name="t.bad", description="bad", handler=lambda a: 1 / 0))
    ok = reg.execute("t.ok", {})
    assert ok["ok"] is True and ok["data"] == {"v": 1} and ok["duration_ms"] >= 0
    bad = reg.execute("t.bad", {})
    assert bad["ok"] is False and "ZeroDivisionError" in bad["error"]


def test_traces_endpoint():
    client.post("/v1/brain/run", json={"goal": "Score my dealer leads", "context": {"leads": LEADS}})
    r = client.get("/v1/brain/traces?limit=3")
    assert r.status_code == 200
    traces = r.json()["traces"]
    assert traces and "spans" in traces[-1]


def test_tool_scopes_listed():
    tools = client.get("/v1/brain/tools").json()["tools"]
    publish = next(t for t in tools if t["name"] == "publishing.publish")
    assert publish["scope"] == "external"
    assert all("scope" in t for t in tools)
