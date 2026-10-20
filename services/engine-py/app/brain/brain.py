"""The Brain: perceive, plan, act through tools, guard, reflect.

Runs inside a harness (app/brain/harness.py) that owns the trace, the
iteration budget, and the retry policy:

  1. Perceive: a context pack is assembled on purpose (context_builder):
     domain grounding, semantic facts, episodic recall, recent session turns,
     each section budgeted.
  2. Plan: the planner picks a skill and emits an explicit plan. If nothing
     matches and nothing ran, the loop may replan once with a domain hint
     inferred from the payload (bounded loop, MAX_ITERATIONS).
  3. Act: compute tools run through the registry's safe execution contract
     (one retry, then degrade with a structured error, never crash).
     Mutating tools are never executed, they become enriched approval
     proposals (risk, expiry, preview).
  4. Guard: drafts pass claim guardrails and the evaluator optimizer loop;
     injection flagged runs lose every approval proposal.
  5. Reflect: the turn, outcome counters, and a session summary are stored.
"""

from typing import Any, Dict, List

from .context_builder import build_context_pack
from .evaluator import optimize_draft
from .harness import MAX_ITERATIONS, TOOL_RETRIES, HarnessRun
from .memory import AgentMemory
from .planner import DeterministicPlanner, Plan
from .shield import MAX_CONTEXT_CHARS, MAX_PLAN_STEPS, context_size, redact_pii, scan_context
from .tools_registry import ToolRegistry, build_default_registry


def _domain_hint(context: Dict[str, Any]) -> str | None:
    if any(k in context for k in ("leads", "records", "metrics", "company_name", "brief")):
        return "marketing"
    if any(k in context for k in ("emails", "events")):
        return "personal"
    return None


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

    def _execute_plan(
        self, run: HarnessRun, plan: Plan, context: Dict[str, Any], goal: str
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        results: Dict[str, Any] = {}
        pending: List[Dict[str, Any]] = []
        for step in plan.steps:
            tool = self.registry.get(step.tool)
            if step.kind == "mutation_proposal" or tool.mutating:
                pending.append(
                    {
                        "tool": step.tool,
                        "status": "pending_approval",
                        "note": step.note,
                        "risk": "high" if tool.scope in ("external", "write") else "medium",
                        "scope": tool.scope,
                        "expires_in_minutes": 30,
                        "preview": step.note,
                    }
                )
                continue
            args = dict(context)
            args.setdefault("query", goal)
            if step.tool == "rag.retrieve":
                args.setdefault(
                    "collection", "domain4s" if plan.domain == "marketing" else "personal"
                )
            outcome = self.registry.execute(step.tool, args)
            attempts = 1
            while not outcome["ok"] and attempts <= TOOL_RETRIES:
                run.span(f"tool:{step.tool}", "retry", "retrying", outcome["duration_ms"], outcome["error"])
                outcome = self.registry.execute(step.tool, args)
                attempts += 1
            if outcome["ok"]:
                results[step.tool] = outcome["data"]
                run.span(f"tool:{step.tool}", "tool", "ok", outcome["duration_ms"])
            else:
                run.degraded = True
                results[step.tool] = {"error": outcome["error"], "degraded": True}
                run.span(f"tool:{step.tool}", "tool", "error", outcome["duration_ms"], outcome["error"])
        return results, pending

    def run(
        self,
        session_id: str,
        goal: str,
        context: Dict[str, Any] | None = None,
        explicit_domain: str | None = None,
    ) -> Dict[str, Any]:
        context = dict(context or {})
        if context_size(context) > MAX_CONTEXT_CHARS:
            raise ValueError("Run budget exceeded: context payload too large for one brain run")

        run = HarnessRun(session_id, goal)
        shield = run.timed("shield.scan", "guard", lambda: scan_context(goal, context))
        pack = run.timed(
            "context.build", "perceive", lambda: build_context_pack(goal, session_id, self.memory)
        )
        grounding = pack["pack"]["grounding"] or pack["pack"]["episodic"]

        plan: Plan = run.timed("planner.plan", "plan", lambda: self.planner.plan(goal, explicit_domain))
        if len(plan.steps) > MAX_PLAN_STEPS:
            plan.steps = plan.steps[:MAX_PLAN_STEPS]

        results, pending_approvals = self._execute_plan(run, plan, context, goal)

        # Bounded replan loop: nothing matched and nothing ran, try once with
        # a domain hint inferred from the payload shape.
        if plan.skill_id is None and not results and not pending_approvals and run.iterations < MAX_ITERATIONS:
            hint = _domain_hint(context)
            if hint and hint != explicit_domain:
                run.iterations += 1
                plan = run.timed(
                    "planner.replan", "plan", lambda: self.planner.plan(goal, hint), f"hint={hint}"
                )
                results, pending_approvals = self._execute_plan(run, plan, context, goal)

        guardrail = None
        draft_evaluation = None
        guardrail_blocks = 0
        draft_text = context.get("draft_text")
        if draft_text:
            outcome = self.registry.execute(
                "guardrails.check_draft",
                {"text": draft_text, "allowed_numbers": context.get("allowed_numbers", [])},
            )
            guardrail = outcome["data"] if outcome["ok"] else {"ok": False, "violations": [], "error": outcome["error"]}
            if not guardrail.get("ok", True):
                guardrail_blocks = len(guardrail.get("violations", []))
            draft_evaluation = run.timed(
                "evaluator.optimize", "guard",
                lambda: optimize_draft(draft_text, grounding_count=len(grounding)),
            )

        blocked_approvals: List[Dict[str, Any]] = []
        if shield["flagged"]:
            blocked_approvals = [
                {**a, "blocked_reason": "prompt_injection_shield", "flagged_fields": shield["fields"]}
                for a in pending_approvals
            ]
            pending_approvals = []

        skill_id = plan.skill_id or "unmatched"
        self.memory.learn(skill_id, approvals_queued=len(pending_approvals), guardrail_blocks=guardrail_blocks)
        summary = (
            f"Skill {plan.skill_id or 'none'} ran {len(results)} compute tool(s), "
            f"queued {len(pending_approvals)} approval(s)."
        )
        self.memory.remember_turn(session_id, redact_pii(goal), plan.skill_id, summary)
        trace = run.finish("degraded" if run.degraded else "ok")

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
            "blocked_approvals": blocked_approvals,
            "shield": shield,
            "draft_evaluation": draft_evaluation,
            "executed_mutations": [],
            "grounding": grounding,
            "guardrail": guardrail,
            "summary": summary,
            "session_summary": self.memory.session_summary(session_id),
            "context_report": pack["report"],
            "trace": trace,
            "memory_insights": self.memory.insights(),
        }
