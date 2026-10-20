"""The Brain: perceive, plan, act through tools, guard, reflect.

Pipeline per run:
  1. Perceive: recall relevant long term memory for the goal.
  2. Plan: the planner picks a skill and emits an explicit plan.
  3. Act: compute tools run immediately. Mutating tools are never executed,
     they are returned as pending approval proposals.
  4. Guard: any draft text in context passes the claim guardrails.
  5. Reflect: the turn and outcome counters are stored in memory.

The brain holds no vendor lock in: planners and LLM providers are strategies
behind interfaces, tools are registry entries, skills are data.
"""

from typing import Any, Dict, List

from .memory import AgentMemory
from .planner import DeterministicPlanner, Plan
from .tools_registry import ToolRegistry, build_default_registry


class Brain:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        planner: DeterministicPlanner | None = None,
        memory: AgentMemory | None = None,
    ) -> None:
        self.registry = registry or build_default_registry()
        self.planner = planner or DeterministicPlanner()
        self.memory = memory or AgentMemory()

    def run(
        self,
        session_id: str,
        goal: str,
        context: Dict[str, Any] | None = None,
        explicit_domain: str | None = None,
    ) -> Dict[str, Any]:
        context = dict(context or {})
        grounding = self.memory.recall(goal)
        plan: Plan = self.planner.plan(goal, explicit_domain)

        results: Dict[str, Any] = {}
        pending_approvals: List[Dict[str, Any]] = []
        for step in plan.steps:
            tool = self.registry.get(step.tool)
            if step.kind == "mutation_proposal" or tool.mutating:
                pending_approvals.append(
                    {"tool": step.tool, "status": "pending_approval", "note": step.note}
                )
                continue
            args = dict(context)
            args.setdefault("query", goal)
            if step.tool == "rag.retrieve":
                args.setdefault(
                    "collection", "domain4s" if plan.domain == "marketing" else "personal"
                )
            results[step.tool] = tool.handler(args)

        guardrail = None
        guardrail_blocks = 0
        draft_text = context.get("draft_text")
        if draft_text:
            guardrail = self.registry.get("guardrails.check_draft").handler(
                {"text": draft_text, "allowed_numbers": context.get("allowed_numbers", [])}
            )
            if not guardrail.get("ok", True):
                guardrail_blocks = len(guardrail.get("violations", []))

        skill_id = plan.skill_id or "unmatched"
        self.memory.learn(skill_id, approvals_queued=len(pending_approvals), guardrail_blocks=guardrail_blocks)
        summary = (
            f"Skill {plan.skill_id or 'none'} ran {len(results)} compute tool(s), "
            f"queued {len(pending_approvals)} approval(s)."
        )
        self.memory.remember_turn(session_id, goal, plan.skill_id, summary)

        return {
            "session_id": session_id,
            "domain": plan.domain,
            "skill_id": plan.skill_id,
            "plan_reason": plan.reason,
            "plan_steps": [
                {"order": s.order, "tool": s.tool, "kind": s.kind, "note": s.note}
                for s in plan.steps
            ],
            "results": results,
            "pending_approvals": pending_approvals,
            "executed_mutations": [],
            "grounding": grounding,
            "guardrail": guardrail,
            "summary": summary,
            "memory_insights": self.memory.insights(),
        }
