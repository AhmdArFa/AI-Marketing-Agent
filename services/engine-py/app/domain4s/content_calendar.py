"""Monthly content calendar from the 4S PLUS pillars.

Follows Marwa Nasr's operating system: one monthly goal, rotating pillars,
a bank of slots with format, hook, and one clear call to action per slot.
"""

from typing import Any, Dict, List

from .catalog import CONTENT_PILLARS

FORMATS = ["reel", "carousel", "single_post", "story_sequence"]
MODULE_ROTATION = ["service", "sales", "spare_parts", "survey", "crm"]
CTA_BY_AUDIENCE = {
    "prospecting": "Book a live demo on your own data",
    "dealer_marketing": "Book your maintenance appointment",
}


def build_calendar(weeks: int, posts_per_week: int, audience: str) -> List[Dict[str, Any]]:
    slots: List[Dict[str, Any]] = []
    idx = 0
    for week in range(1, weeks + 1):
        for _ in range(posts_per_week):
            pillar = CONTENT_PILLARS[idx % len(CONTENT_PILLARS)]
            module = MODULE_ROTATION[idx % len(MODULE_ROTATION)]
            slots.append(
                {
                    "week": week,
                    "pillar": pillar["name"],
                    "module_focus": module,
                    "format": FORMATS[idx % len(FORMATS)],
                    "hook": pillar["angle"],
                    "cta": CTA_BY_AUDIENCE[audience],
                }
            )
            idx += 1
    return slots
