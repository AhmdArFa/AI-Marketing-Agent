"""Evaluator optimizer loop for marketing drafts (Anthropic pattern).

One component evaluates against explicit criteria, another revises, and the
loop repeats for a bounded number of iterations. The evaluator here is
deterministic, so scores are reproducible and testable: guardrail compliance,
call to action presence, length discipline, and grounding. An LLM judge can
be added behind evaluate_draft later without changing the loop.
"""

import re
from typing import Any, Dict, List

from ..domain4s.guardrails import check_draft

CTA_TERMS = ["book", "demo", "احجز", "تواصل", "سجل", "اطلب", "call", "register"]
MAX_WORDS = 120
MIN_WORDS = 12


def evaluate_draft(text: str, grounding_count: int = 0) -> Dict[str, Any]:
    words = text.split()
    guard = check_draft(text)
    lower = text.lower()
    checks = {
        "guardrail_clean": guard["ok"],
        "has_cta": any(t in lower for t in CTA_TERMS),
        "length_ok": MIN_WORDS <= len(words) <= MAX_WORDS,
        "grounded": grounding_count > 0 or "%" not in text,
    }
    weights = {"guardrail_clean": 40, "has_cta": 20, "length_ok": 15, "grounded": 25}
    score = sum(w for k, w in weights.items() if checks[k])
    return {"score": score, "checks": checks, "violations": guard["violations"]}


def _revise(text: str, evaluation: Dict[str, Any]) -> str:
    sentences = re.split(r"(?<=[.!؟?])\s+", text.strip())
    if not evaluation["checks"]["guardrail_clean"]:
        bad_terms = ["guarantee", "guaranteed", "نتائج مضمونة", "بنضمن", "%"]
        sentences = [
            s for s in sentences
            if not any(t in s.lower() for t in bad_terms)
        ]
    text = " ".join(s for s in sentences if s)
    if not evaluation["checks"]["has_cta"]:
        text = (text + " Book a live demo on your own data.").strip()
    if len(text.split()) > MAX_WORDS:
        text = " ".join(text.split()[:MAX_WORDS]).rstrip(",;:") + "."
    return text


def optimize_draft(
    text: str, grounding_count: int = 0, max_iterations: int = 2
) -> Dict[str, Any]:
    history: List[Dict[str, Any]] = []
    current = text
    for i in range(max_iterations + 1):
        evaluation = evaluate_draft(current, grounding_count)
        history.append({"iteration": i, "score": evaluation["score"], "checks": evaluation["checks"]})
        if evaluation["score"] >= 100 or i == max_iterations:
            break
        revised = _revise(current, evaluation)
        if revised == current:
            break
        current = revised
    return {
        "final_text": current,
        "final_score": history[-1]["score"],
        "iterations": history,
        "improved": history[-1]["score"] > history[0]["score"],
    }
