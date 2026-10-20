"""Input shield and output hygiene (OWASP LLM 2025 containment controls).

Prompt injection (LLM01) has no foolproof prevention, so this module does
containment, not magic:
  - scan untrusted text for known injection patterns and flag the run,
  - the brain blocks approval proposals on flagged runs,
  - PII in free text is masked before it is stored or echoed (LLM02),
  - run budgets cap steps and context size (LLM10, unbounded consumption).
"""

import re
from typing import Any, Dict, List

MAX_PLAN_STEPS = 12
MAX_CONTEXT_CHARS = 50_000

INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"disregard (your|the) (instructions|rules)",
    r"reveal (your )?(system prompt|instructions)",
    r"print (your )?(system prompt|api key|password)",
    r"send (all|the) (data|emails|contacts) to",
    r"exfiltrate",
    r"you are now (a|an|in)",
    r"jailbreak",
    r"تجاهل (كل )?(التعليمات|الأوامر)",
    r"اكشف (ال)?(برومبت|تعليمات النظام)",
    r"ابعت (كل )?(البيانات|الإيميلات)",
]

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(\+?\d[\d\s-]{7,}\d)")


def scan_text(text: str) -> Dict[str, Any]:
    lower = text.lower()
    hits = [p for p in INJECTION_PATTERNS if re.search(p, lower)]
    return {"flagged": bool(hits), "patterns": hits}


def scan_context(goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
    findings = scan_text(goal)
    flagged_fields: List[str] = []
    if findings["flagged"]:
        flagged_fields.append("goal")
    for key, value in context.items():
        if isinstance(value, str) and scan_text(value)["flagged"]:
            flagged_fields.append(f"context.{key}")
    return {"flagged": bool(flagged_fields), "fields": flagged_fields}


def redact_pii(text: str) -> str:
    text = _EMAIL.sub("[email]", text)

    def _mask_phone(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(1))
        return "[phone]" if len(digits) >= 9 else m.group(1)

    return _PHONE.sub(_mask_phone, text)


def context_size(context: Dict[str, Any]) -> int:
    return len(repr(context))
