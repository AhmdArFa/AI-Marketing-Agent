"""Agent memory (Repository pattern over short term and long term stores).

Short term: per session conversation turns, bounded.
Long term: notes in the personal knowledge base, recalled by retrieval.
Learning log: outcome counters per skill, so the brain can report which
skills actually succeed and surface simple, honest insights. No hidden state:
everything here is inspectable through these methods.
"""

from collections import defaultdict, deque
from typing import Any, Deque, Dict, List

from ..pipelines.rag import KB


class AgentMemory:
    def __init__(self, max_turns_per_session: int = 50) -> None:
        # Memory kinds, kept explicit (see docs/RESEARCH_NOTES.md section 4):
        # working and episodic: per session turns below.
        # semantic: distilled facts, stored through remember_fact.
        # procedural: the skill manifests themselves, loaded by the planner.
        self._facts: Dict[str, str] = {}
        self._turns: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=max_turns_per_session)
        )
        self._outcomes: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"runs": 0, "approvals_queued": 0, "guardrail_blocks": 0}
        )

    def remember_turn(self, session_id: str, goal: str, skill_id: str | None, summary: str) -> None:
        self._turns[session_id].append({"goal": goal, "skill": skill_id, "summary": summary})

    def recent_turns(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        return list(self._turns.get(session_id, deque()))[-limit:]

    def recall(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        hits = KB.personal.search(query, top_k=top_k) + KB.domain4s.search(query, top_k=top_k)
        hits.sort(key=lambda h: h[1], reverse=True)
        return [{"doc_id": d, "score": s, "snippet": snip} for d, s, snip in hits[:top_k]]

    def remember_fact(self, key: str, value: str) -> None:
        """Semantic memory: one distilled fact, retrievable by key and by search."""
        self._facts[key] = value
        KB.personal.add_document(f"fact:{key}", f"{key}: {value}")

    def recall_facts(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        hits = KB.personal.search(query, top_k=top_k * 2)
        facts = [
            {"doc_id": d, "score": s, "snippet": snip}
            for d, s, snip in hits
            if d.startswith("fact:")
        ]
        return facts[:top_k]

    def fact(self, key: str) -> str | None:
        return self._facts.get(key)

    def learn(self, skill_id: str, approvals_queued: int, guardrail_blocks: int) -> None:
        stats = self._outcomes[skill_id]
        stats["runs"] += 1
        stats["approvals_queued"] += approvals_queued
        stats["guardrail_blocks"] += guardrail_blocks

    def insights(self) -> Dict[str, Any]:
        return {
            skill: dict(stats)
            for skill, stats in self._outcomes.items()
        }
