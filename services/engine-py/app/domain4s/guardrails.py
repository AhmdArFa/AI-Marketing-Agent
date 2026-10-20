"""Claim guardrails for every draft the agent produces about 4S PLUS.

Two checks: prohibited phrases from the catalog, and percentages that are not
backed by an allowed, sourced number. Flags go back to the human approver.
"""

import re
from typing import List

from .catalog import PROHIBITED_CLAIMS

_PCT = re.compile(r"(\d+(?:\.\d+)?\s*%)")


def check_draft(text: str, allowed_numbers: List[str] | None = None) -> dict:
    allowed = set(allowed_numbers or [])
    lower = text.lower()
    violations: List[str] = []

    matched = [p for p in PROHIBITED_CLAIMS if p in lower]
    # Longest match wins, so "guaranteed results" is not double counted as "guarantee".
    matched.sort(key=len, reverse=True)
    kept: List[str] = []
    for phrase in matched:
        if not any(phrase in longer for longer in kept):
            kept.append(phrase)
    for phrase in kept:
        violations.append(f"Prohibited claim: '{phrase}'")

    for match in _PCT.findall(text):
        if match.replace(" ", "") not in {a.replace(" ", "") for a in allowed}:
            violations.append(f"Unverified percentage in draft: '{match}' needs a source or removal")

    return {"ok": not violations, "violations": violations}
