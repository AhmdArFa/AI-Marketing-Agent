import os

import pytest
from fastapi.testclient import TestClient

from app.brain import Brain
from app.main import app

client = TestClient(app)

LEADS = [
    {
        "company": "Delta Motors",
        "business_type": "dealer",
        "branches": 3,
        "monthly_jobs_or_sales": 240,
        "current_system": "excel",
        "signals": ["demo_requested", "replied"],
        "days_since_last_touch": 2,
    }
]


def test_brain_picks_lead_scoring_skill_and_never_executes_mutations():
    r = client.post(
        "/v1/brain/run",
        json={"session_id": "s1", "goal": "Score my dealer leads and follow up", "context": {"leads": LEADS}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["skill_id"] == "prospect_lead_scoring"
    assert body["executed_mutations"] == []
    assert body["pending_approvals"][0]["tool"] == "crm.create_followup_task"
    assert body["results"]["domain4s.score_leads"]["scored"][0]["tier"] == "hot"


def test_brain_retention_skill_with_arabic_goal():
    r = client.post(
        "/v1/brain/run",
        json={
            "session_id": "s2",
            "goal": "ابعت تذكير صيانة مستحقة للعملاء",
            "context": {
                "records": [
                    {"customer": "Omar", "chassis": "CH1", "months_since_last_service": 7, "km_since_last_service": 4000}
                ]
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["skill_id"] == "dealer_retention_campaign"
    assert body["results"]["domain4s.retention_segments"]["segments"][0]["segment"] == "maintenance_due"


def test_brain_guardrail_blocks_bad_draft():
    r = client.post(
        "/v1/brain/run",
        json={
            "session_id": "s3",
            "goal": "Analyze my campaign ROAS",
            "context": {
                "metrics": [
                    {"campaign": "A", "spend": 100, "impressions": 1000, "clicks": 50, "conversions": 5, "revenue": 300}
                ],
                "draft_text": "Guaranteed results, 40% more sales for everyone",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["guardrail"]["ok"] is False
    assert body["memory_insights"]


def test_brain_catalog_endpoints():
    skills = client.get("/v1/brain/skills").json()["skills"]
    assert len(skills) == 6
    tools = client.get("/v1/brain/tools").json()["tools"]
    mutating = [t for t in tools if t["mutating"]]
    assert mutating and all(t["requires_approval"] for t in mutating)


def test_security_headers_present():
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    body = r.json()
    assert body["skills_loaded"] == 6
    assert body["tools_registered"] >= 10


def test_api_key_enforced_when_configured(monkeypatch):
    monkeypatch.setenv("ENGINE_API_KEY", "test-secret-key")
    secure_client = TestClient(app)
    assert secure_client.get("/health").status_code == 200  # health stays public
    assert secure_client.post("/v1/brain/run", json={"goal": "Score leads"}).status_code == 401
    ok = secure_client.post(
        "/v1/brain/run",
        json={"goal": "Score my leads", "context": {"leads": LEADS}},
        headers={"X-API-Key": "test-secret-key"},
    )
    assert ok.status_code == 200
    wrong_role = secure_client.post(
        "/v1/rag/ingest",
        json={"collection": "brand", "doc_id": "x", "text": "alpha bravo charlie secure ingest payload"},
        headers={"X-API-Key": "test-secret-key", "X-Role": "viewer"},
    )
    assert wrong_role.status_code == 403
    right_role = secure_client.post(
        "/v1/rag/ingest",
        json={"collection": "brand", "doc_id": "x", "text": "alpha bravo charlie secure ingest payload"},
        headers={"X-API-Key": "test-secret-key", "X-Role": "operator"},
    )
    assert right_role.status_code == 200


def test_brain_is_deterministic_for_same_goal():
    brain = Brain()
    a = brain.run("det", "Score my dealer leads", {"leads": LEADS})
    b = brain.run("det", "Score my dealer leads", {"leads": LEADS})
    assert a["skill_id"] == b["skill_id"] == "prospect_lead_scoring"
    assert a["plan_steps"] == b["plan_steps"]
