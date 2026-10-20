"""Prospect lead scoring for selling 4S PLUS.

Implements the scoring idea from Shahd's CRM automation deck with explicit,
explainable rules. Every score ships with its reasons, so a human can trust
or override it. An ML model can replace the weights later behind this API.
"""

from typing import Any, Dict, List

BUSINESS_FIT = {"dealer": 25, "workshop": 25, "parts_trader": 18, "fleet": 15, "other": 5}
SIGNAL_POINTS = {
    "demo_requested": 25,
    "pricing_page": 15,
    "replied": 12,
    "referral": 12,
    "event_meeting": 10,
    "website_visit": 4,
}
PAIN_POINTS = {"paper": 12, "excel": 10, "none": 6, "other_erp": 3}


def score_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []

    fit = BUSINESS_FIT.get(str(lead.get("business_type", "other")), 5)
    score += fit
    reasons.append(f"Business type fit: {lead.get('business_type')} (+{fit})")

    volume = int(lead.get("monthly_jobs_or_sales", 0))
    volume_points = 15 if volume >= 200 else 10 if volume >= 80 else 5 if volume >= 20 else 0
    if volume_points:
        score += volume_points
        reasons.append(f"Monthly volume {volume} (+{volume_points})")

    branches = int(lead.get("branches", 1))
    if branches > 1:
        points = min(5 + branches, 12)
        score += points
        reasons.append(f"Multi branch operation, {branches} branches (+{points})")

    pain = PAIN_POINTS.get(str(lead.get("current_system", "excel")), 0)
    if pain:
        score += pain
        reasons.append(f"Current system '{lead.get('current_system')}' signals manual pain (+{pain})")

    for signal in lead.get("signals", []):
        points = SIGNAL_POINTS.get(signal, 0)
        if points:
            score += points
            reasons.append(f"Signal {signal} (+{points})")

    days = int(lead.get("days_since_last_touch", 999))
    if days <= 7:
        score += 5
        reasons.append("Touched within the last week (+5)")
    elif days > 90:
        score -= 10
        reasons.append("Cold for over 90 days (-10)")

    score = max(0, min(score, 100))
    tier = "hot" if score >= 65 else "warm" if score >= 40 else "cold"
    next_action = {
        "hot": "Call today and offer a live demo on their own data",
        "warm": "Send the One Car Journey story, then follow up in 3 days",
        "cold": "Add to the monthly education sequence, no direct pitch yet",
    }[tier]
    return {
        "company": lead.get("company", "unknown"),
        "score": score,
        "tier": tier,
        "reasons": reasons,
        "next_action": next_action,
    }


def score_leads(leads: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = sorted((score_lead(l) for l in leads), key=lambda s: s["score"], reverse=True)
    return {"scored": scored, "hot_count": sum(1 for s in scored if s["tier"] == "hot")}
