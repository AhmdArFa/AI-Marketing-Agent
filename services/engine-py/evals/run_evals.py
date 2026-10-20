"""Golden dataset evaluation harness.

Runs the shipped golden cases against the real pipelines (no HTTP, no model
calls) and reports per case pass or fail plus aggregate rates. Retrieval is
scored by hit at rank 1 against the expected document, the deterministic
equivalent of the recall checks described in docs/RESEARCH_NOTES.md.
Run directly:  python -m evals.run_evals     (exit code 1 on any failure)
Or through pytest: tests/test_evals.py wraps evaluate_all().
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain4s.campaign_brief import build_campaign_brief
from app.domain4s.guardrails import check_draft
from app.domain4s.lead_scoring import score_lead
from app.domain4s.retention import build_retention_segments
from app.pipelines.rag import KB

GOLDEN = Path(__file__).parent / "golden.jsonl"


def _run_case(case: Dict[str, Any]) -> bool:
    kind = case["kind"]
    if kind == "retrieval":
        hits = KB.get(case["collection"]).search(case["query"], top_k=3)
        return bool(hits) and hits[0][0] == case["expect_top"]
    if kind == "lead_score":
        return score_lead(case["lead"])["tier"] == case["expect_tier"]
    if kind == "retention":
        segments = build_retention_segments([case["record"]])
        return any(
            s["segment"] == case["expect_segment"]
            and any(c["customer"] == case["record"]["customer"] for c in s["customers"])
            for s in segments
        )
    if kind == "guardrail":
        return check_draft(case["text"])["ok"] == case["expect_ok"]
    if kind == "brain_shield":
        from app.brain import Brain

        out = Brain().run("eval-shield", case["goal"], case.get("context", {}))
        return (
            len(out["blocked_approvals"]) >= case["expect_blocked_min"]
            and out["executed_mutations"] == []
            and out["trace"]["status"] in ("ok", "degraded")
        )
    if kind == "brain_budget":
        from app.brain import Brain

        try:
            Brain().run("eval-budget", "Score my leads", {"blob": "x" * 60000})
            return False
        except ValueError:
            return True
    if kind == "campaign_brief":
        brief = build_campaign_brief(case["answers"])
        if brief["complete"] != case["expect_complete"]:
            return False
        needle = case.get("expect_missing_contains")
        return needle is None or needle in brief["missing_fields"]
    raise ValueError(f"Unknown golden case kind: {kind}")


def evaluate_all() -> Dict[str, Any]:
    cases: List[Dict[str, Any]] = [
        json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    results = []
    for case in cases:
        try:
            passed = _run_case(case)
        except Exception as exc:  # a crashing case is a failing case
            passed = False
            results.append({"id": case["id"], "passed": False, "error": str(exc)})
            continue
        results.append({"id": case["id"], "passed": passed})
    passed_count = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": passed_count,
        "pass_rate": round(passed_count / max(len(results), 1), 4),
        "results": results,
    }


if __name__ == "__main__":
    report = evaluate_all()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["pass_rate"] == 1.0 else 1)
