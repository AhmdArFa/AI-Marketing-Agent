"""Campaign brief builder (brief first, plan second).

Implements the rule from the content strategy template: never jump from raw
brief answers to a content plan. The builder checks completeness first and
reports missing fields instead of inventing them, then assembles audiences,
pillars, cadence, and KPIs from the domain catalog.
"""

from typing import Any, Dict, List

from .catalog import CONTENT_PILLARS, PRODUCT_PILLARS, PROSPECT_PERSONAS

REQUIRED_FIELDS = ["product_focus", "audience_type", "monthly_goal"]

KPI_BY_GOAL = {
    "demos": ["demo bookings", "demo show rate", "hot lead count"],
    "appointments": ["appointments booked per 100 reminders", "no show rate", "winback rate"],
    "awareness": ["reach", "saves and shares per post", "profile visits to demo page rate"],
}


def build_campaign_brief(answers: Dict[str, Any]) -> Dict[str, Any]:
    missing = [f for f in REQUIRED_FIELDS if not answers.get(f)]
    focus = str(answers.get("product_focus", "service"))
    audience_type = str(answers.get("audience_type", "prospecting"))
    goal = str(answers.get("monthly_goal", "demos"))

    if audience_type == "prospecting":
        audiences = [p["title"] for p in PROSPECT_PERSONAS]
    else:
        audiences = ["Car owners due for periodic maintenance", "Survey detractors and promoters"]

    pillars = [p["name"] for p in CONTENT_PILLARS]
    if focus in PRODUCT_PILLARS:
        pillars = sorted(pillars, key=lambda name: 0 if focus in name.lower() else 1)

    channels = answers.get("channels") or ["linkedin", "facebook"]
    cadence = {
        "posts_per_week": 3,
        "channels": channels,
        "review_cycle": "Measure at 1 hour, 6 hours, 24 hours, 48 hours, and one week after publishing",
        "monthly_loop": "Analyze, extract insights, adjust pillars and scoring, repeat",
    }

    return {
        "complete": not missing,
        "missing_fields": missing,
        "product_focus": focus,
        "audience_type": audience_type,
        "audiences": audiences,
        "pillars": pillars,
        "cadence": cadence,
        "kpis": KPI_BY_GOAL.get(goal, KPI_BY_GOAL["demos"]),
        "guardrails": [
            "One clear call to action per post",
            "No guaranteed results claims, no unverified percentages",
            "Nothing publishes without human approval",
        ],
        "next_step": (
            "Fill the missing fields, then generate the content calendar"
            if missing
            else "Generate the content calendar from these pillars"
        ),
    }
