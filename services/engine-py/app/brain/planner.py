"""Planner (Strategy pattern).

V1 is a deterministic planner: it scores skill manifests against the goal
and produces an explicit, inspectable plan before anything runs. An LLM
planner can replace this class behind the same interface when live model
keys are configured, without changing the brain or the API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .skills import Skill, load_skills, pick_skill


@dataclass
class PlanStep:
    order: int
    tool: str
    kind: str  # compute | mutation_proposal
    note: str


@dataclass
class Plan:
    skill_id: str | None
    domain: str
    steps: List[PlanStep] = field(default_factory=list)
    reason: str = ""


class DeterministicPlanner:
    def __init__(self) -> None:
        self.skills = load_skills()

    def plan(self, goal: str, explicit_domain: str | None = None) -> Plan:
        skill: Skill | None = pick_skill(self.skills, goal, explicit_domain)
        if skill is None:
            return Plan(
                skill_id=None,
                domain=explicit_domain or "marketing",
                steps=[PlanStep(1, "rag.retrieve", "compute", "No skill matched, ground the goal first")],
                reason="No skill triggers matched. Falling back to retrieval so a human can route it.",
            )
        steps: List[PlanStep] = [
            PlanStep(i + 1, step.tool, "compute", f"Skill step from manifest {skill.id}")
            for i, step in enumerate(skill.steps)
        ]
        if skill.follow_up_tool:
            steps.append(
                PlanStep(len(steps) + 1, skill.follow_up_tool, "mutation_proposal", "Queued for human approval, never auto executed")
            )
        return Plan(
            skill_id=skill.id,
            domain=skill.domain,
            steps=steps,
            reason=f"Skill '{skill.id}' matched the goal triggers.",
        )

    def skill_for(self, plan: Plan) -> Skill | None:
        for s in self.skills:
            if s.id == plan.skill_id:
                return s
        return None
