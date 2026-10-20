"""Skills (pluggable capability bundles).

A skill is a declarative manifest: when it triggers, which tools it runs in
order, what its mutation policy is, and which guardrails apply. Manifests are
JSON files in app/brain/skills/, so new skills are added without code changes
to the brain itself. This mirrors the skill idea used by agent frameworks:
named, bounded, reviewable units of behavior.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

SKILLS_DIR = Path(__file__).parent / "skills"


@dataclass
class SkillStep:
    tool: str
    args_from: str = "context"  # where the step reads its arguments: context key


@dataclass
class Skill:
    id: str
    name: str
    domain: str
    description: str
    triggers: List[str]
    steps: List[SkillStep]
    follow_up_tool: str | None = None  # mutating tool proposed after the steps
    guardrails: List[str] = field(default_factory=list)

    def trigger_score(self, text: str) -> int:
        lower = text.lower()
        return sum(1 for t in self.triggers if t.lower() in lower)


def load_skills(directory: Path = SKILLS_DIR) -> List[Skill]:
    skills: List[Skill] = []
    for path in sorted(directory.glob("*.json")):
        raw: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        skills.append(
            Skill(
                id=raw["id"],
                name=raw["name"],
                domain=raw["domain"],
                description=raw.get("description", ""),
                triggers=raw.get("triggers", []),
                steps=[SkillStep(**s) for s in raw.get("steps", [])],
                follow_up_tool=raw.get("follow_up_tool"),
                guardrails=raw.get("guardrails", []),
            )
        )
    return skills


def pick_skill(skills: List[Skill], goal_text: str, explicit_domain: str | None = None) -> Skill | None:
    candidates = [s for s in skills if explicit_domain is None or s.domain == explicit_domain]
    scored = sorted(candidates, key=lambda s: s.trigger_score(goal_text), reverse=True)
    if scored and scored[0].trigger_score(goal_text) > 0:
        return scored[0]
    return None
