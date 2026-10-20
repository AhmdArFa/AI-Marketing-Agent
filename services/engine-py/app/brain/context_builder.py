"""Context engineering: the context pack is assembled on purpose, not dumped.

Sections in priority order, each with a size budget, so the most decision
relevant material survives and the rest is dropped loudly (recorded in the
report) instead of silently pushing the good parts out:

  1. task: the goal itself and the caller's payload keys (never truncated).
  2. domain grounding: top retrieval hits for the goal from the domain KB.
  3. semantic facts: distilled long term facts relevant to the goal.
  4. episodic recall: what this agent remembers doing about similar goals.
  5. session recent: the last turns of this session, shortest lifetime first
     to be dropped when the budget is tight.
"""

from typing import Any, Dict, List

from ..pipelines.rag import KB

PACK_BUDGET_CHARS = 12_000
SECTION_CAPS = {"grounding": 4_000, "facts": 2_000, "episodic": 3_000, "session": 2_000}


def _trim(items: List[Dict[str, Any]], cap: int) -> tuple[List[Dict[str, Any]], int]:
    kept, used = [], 0
    for item in items:
        size = len(str(item))
        if used + size > cap:
            break
        kept.append(item)
        used += size
    return kept, len(items) - len(kept)


def build_context_pack(goal: str, session_id: str, memory: Any) -> Dict[str, Any]:
    grounding_raw = KB.domain4s.search(goal, top_k=4)
    grounding = [
        {"doc_id": d, "score": s, "snippet": snip} for d, s, snip in grounding_raw
    ]
    facts = memory.recall_facts(goal, top_k=4)
    episodic = memory.recall(goal)
    session = memory.recent_turns(session_id, limit=3)

    pack: Dict[str, Any] = {"goal": goal}
    report: Dict[str, Any] = {"budget_chars": PACK_BUDGET_CHARS, "sections": {}, "dropped": {}}

    for name, items in (
        ("grounding", grounding),
        ("facts", facts),
        ("episodic", episodic),
        ("session", session),
    ):
        kept, dropped = _trim(items, SECTION_CAPS[name])
        pack[name] = kept
        report["sections"][name] = len(str(kept))
        if dropped:
            report["dropped"][name] = dropped

    report["used_chars"] = sum(report["sections"].values()) + len(goal)
    return {"pack": pack, "report": report}
