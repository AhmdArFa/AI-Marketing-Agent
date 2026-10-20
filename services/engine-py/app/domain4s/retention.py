"""Dealer retention segments computed from 4S PLUS service and survey data.

These are the campaigns a dealer runs with the system, and the proof stories
Vo Technology markets with. Rules are deterministic and auditable.
"""

from typing import Any, Dict, List


def build_retention_segments(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    due, lapsed, detractors, promoters = [], [], [], []

    for r in records:
        if r.get("open_jobcard"):
            continue
        customer = {"customer": r.get("customer"), "chassis": r.get("chassis")}

        survey = r.get("last_survey_score")
        if survey is not None and survey <= 6:
            detractors.append({**customer, "survey_score": survey})
            continue
        if survey is not None and survey >= 9:
            promoters.append({**customer, "survey_score": survey})

        months = float(r.get("months_since_last_service", 0))
        km = int(r.get("km_since_last_service", 0))
        interval_m = int(r.get("service_interval_months", 6))
        interval_km = int(r.get("service_interval_km", 10000))
        if months >= interval_m * 2 or km >= interval_km * 2:
            lapsed.append({**customer, "months_since_last_service": months})
        elif months >= interval_m or km >= interval_km:
            due.append(
                {
                    **customer,
                    "months_since_last_service": months,
                    "km_since_last_service": km,
                }
            )

    segments = []
    if due:
        segments.append(
            {
                "segment": "maintenance_due",
                "customers": due,
                "playbook": "periodic_maintenance_reminder",
                "channel": "whatsapp_then_call",
                "human_first": False,
            }
        )
    if lapsed:
        segments.append(
            {
                "segment": "lapsed_winback",
                "customers": lapsed,
                "playbook": "lapsed_winback_with_service_package",
                "channel": "call_first",
                "human_first": True,
            }
        )
    if detractors:
        segments.append(
            {
                "segment": "survey_detractors",
                "customers": detractors,
                "playbook": "detractor_recovery",
                "channel": "human_call_only",
                "human_first": True,
            }
        )
    if promoters:
        segments.append(
            {
                "segment": "survey_promoters",
                "customers": promoters,
                "playbook": "promoter_review_and_referral",
                "channel": "whatsapp",
                "human_first": False,
            }
        )
    return segments
