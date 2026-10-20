"""Personal pipelines: inbox triage scoring and daily briefing synthesis."""

from typing import Any, Dict, List

URGENT_TERMS = ["urgent", "deadline", "invoice", "contract", "security", "عاجل", "موعد", "فاتورة"]
ACTION_TERMS = ["please", "review", "approve", "reply", "send", "confirm", "راجع", "أكد"]


def triage_emails(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    scored = []
    for mail in emails:
        text = f"{mail.get('subject', '')} {mail.get('snippet', '')}".lower()
        score = 0
        if any(t in text for t in URGENT_TERMS):
            score += 2
        if any(t in text for t in ACTION_TERMS):
            score += 1
        priority = "high" if score >= 3 else "medium" if score >= 1 else "low"
        scored.append({**mail, "priority": priority, "score": score})
    return sorted(scored, key=lambda m: m["score"], reverse=True)


def build_daily_briefing(events: List[Dict[str, Any]], emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    triaged = triage_emails(emails)
    high = [m for m in triaged if m["priority"] == "high"]
    return {
        "event_count": len(events),
        "events": events,
        "priority_emails": high,
        "inbox_total": len(emails),
        "focus_blocks": ["09:30 to 11:30 Deep Work", "14:00 to 15:00 Follow ups"],
        "headline": (
            f"{len(events)} event(s) today, {len(high)} high priority email(s) "
            f"out of {len(emails)} unread."
        ),
    }
