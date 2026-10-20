from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ROWS = [
    {"campaign": "Search A", "spend": 420.5, "impressions": 24500, "clicks": 890, "conversions": 28, "revenue": 1680.0},
    {"campaign": "Social B", "spend": 310.0, "impressions": 19200, "clicks": 740, "conversions": 31, "revenue": 620.0},
]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_campaign_analytics_math():
    r = client.post("/v1/analytics/campaign", json={"rows": ROWS})
    assert r.status_code == 200
    body = r.json()
    assert body["totals"]["spend"] == 730.5
    assert body["totals"]["conversions"] == 59
    assert body["totals"]["cpa"] == 12.38
    assert body["best_campaign"] == "Search A"


def test_marketing_execute_returns_pending_action_shape():
    r = client.post(
        "/v1/engine/execute",
        json={
            "domain": "marketing",
            "task_type": "campaign_analysis",
            "user_query": "Analyze my campaign and draft a post",
            "context_data": {"metrics": ROWS},
            "brand_voice_id": "growth-b2b-v1",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["structured_output"]["computed_metrics"]["totals"]["roas"] > 0
    assert body["recommended_actions"][0]["suggested_tool"] == "social.scheduleDraft"


def test_personal_briefing_and_triage():
    r = client.post(
        "/v1/engine/execute",
        json={
            "domain": "personal",
            "task_type": "daily_briefing",
            "user_query": "Give me my daily briefing",
            "context_data": {
                "calendar_events": [{"title": "Product Sync", "start": "11:30"}],
                "emails": [{"subject": "Urgent: please review the contract", "sender": "legal@example.com"}],
            },
        },
    )
    assert r.status_code == 200
    briefing = r.json()["structured_output"]["briefing"]
    assert briefing["event_count"] == 1
    assert len(briefing["priority_emails"]) == 1


def test_rag_retrieves_brand_voice():
    r = client.post("/v1/rag/retrieve", json={"collection": "brand", "query": "brand voice simple Arabic", "top_k": 2})
    assert r.status_code == 200
    hits = r.json()["hits"]
    assert hits and hits[0]["doc_id"] == "brand/voice-v1"
