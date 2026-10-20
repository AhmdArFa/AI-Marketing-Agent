from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_lead_scoring_hot_dealer():
    r = client.post(
        "/v1/domain4s/lead-score",
        json={
            "leads": [
                {
                    "company": "Delta Motors",
                    "business_type": "dealer",
                    "branches": 3,
                    "monthly_jobs_or_sales": 240,
                    "current_system": "excel",
                    "signals": ["demo_requested", "replied"],
                    "days_since_last_touch": 2,
                },
                {
                    "company": "Small Corner Workshop",
                    "business_type": "other",
                    "monthly_jobs_or_sales": 5,
                    "current_system": "other_erp",
                    "signals": [],
                    "days_since_last_touch": 200,
                },
            ]
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["hot_count"] == 1
    assert body["scored"][0]["company"] == "Delta Motors"
    assert body["scored"][0]["tier"] == "hot"
    assert body["scored"][0]["reasons"]


def test_retention_segments_from_service_data():
    r = client.post(
        "/v1/domain4s/retention",
        json={
            "records": [
                {"customer": "Omar", "chassis": "CH1", "months_since_last_service": 7, "km_since_last_service": 4000},
                {"customer": "Sara", "chassis": "CH2", "months_since_last_service": 15, "km_since_last_service": 3000},
                {"customer": "Karim", "chassis": "CH3", "months_since_last_service": 1, "last_survey_score": 4},
                {"customer": "Laila", "chassis": "CH4", "months_since_last_service": 2, "last_survey_score": 10},
                {"customer": "In Workshop Now", "chassis": "CH5", "months_since_last_service": 9, "open_jobcard": True},
            ]
        },
    )
    assert r.status_code == 200
    segments = {s["segment"]: s for s in r.json()["segments"]}
    assert [c["customer"] for c in segments["maintenance_due"]["customers"]] == ["Omar"]
    assert segments["lapsed_winback"]["human_first"] is True
    assert segments["survey_detractors"]["channel"] == "human_call_only"
    assert "survey_promoters" in segments
    all_customers = [c["customer"] for s in segments.values() for c in s["customers"]]
    assert "In Workshop Now" not in all_customers


def test_content_calendar_uses_pillars_and_cta():
    r = client.post(
        "/v1/domain4s/content-calendar",
        json={"weeks": 4, "posts_per_week": 3, "audience": "prospecting"},
    )
    assert r.status_code == 200
    slots = r.json()["slots"]
    assert len(slots) == 12
    assert all(s["cta"] == "Book a live demo on your own data" for s in slots)
    assert len({s["pillar"] for s in slots}) == 5


def test_guardrails_flag_guarantee_and_unverified_percent():
    r = client.post(
        "/v1/domain4s/guardrails/check",
        json={"text": "We offer guaranteed results and 40% more sales with 4S PLUS."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert len(body["violations"]) == 2


def test_guardrails_pass_clean_draft():
    r = client.post(
        "/v1/domain4s/guardrails/check",
        json={"text": "Follow one car from sale to survey, all in 4S PLUS. Book a live demo."},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_domain_rag_collection():
    r = client.post(
        "/v1/rag/retrieve",
        json={"collection": "domain4s", "query": "JobCard lifecycle Ready for invoicing", "top_k": 2},
    )
    assert r.status_code == 200
    hits = r.json()["hits"]
    assert hits and hits[0]["doc_id"] == "domain4s/service-jobcard"
