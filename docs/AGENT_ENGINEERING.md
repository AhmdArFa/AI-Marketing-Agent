# Agent Engineering: The Chosen Approach per Discipline

For each of the ten agent engineering disciplines, this document records the
approach chosen for this product, where it lives in the code, and what was
rejected and why. Choices favor determinism and auditability over autonomy
for its own sake, following the production evidence in
docs/RESEARCH_NOTES.md.

## 1. Harness Engineering

Chosen: a dedicated run harness (`app/brain/harness.py`) that owns the run
id, span trace, iteration budget, retry policy, and a bounded recent trace
store. The brain never runs loose; every run lives inside the harness.
Rejected: ad hoc logging inside each component. A bad run must be replayable
from its trace alone, which scattered logs cannot give.

## 2. Loop Engineering

Chosen: a bounded perceive, plan, act, guard, reflect loop with at most one
replan (domain hint inferred from payload shape when nothing matched) and
exactly one retry per failing compute tool, then degrade with a structured
error. Rejected: open ended agent loops and unbounded self correction; they
compound errors and cost, and marketing tasks here have known shapes.

## 3. Context Engineering

Chosen: an explicit context pack (`app/brain/context_builder.py`) assembled
in priority order: task, domain grounding, semantic facts, episodic recall,
recent session turns, each with its own char budget and a report that records
what was dropped. Rejected: stuffing the whole history and knowledge base
into the prompt (lost in the middle effects, silent quality loss).

## 4. Tool Design

Chosen: a registry of small, single purpose tools with typed input schemas,
a permission scope per tool, and one safe execution contract that returns
{ok, data or error, duration, truncated} and never raises into the loop
(`app/brain/tools_registry.py`). Tool outputs are capped and summarized.
Rejected: a few mega tools with free form payloads, and letting tool
exceptions crash runs.

## 5. Memory Architecture

Chosen: four explicit kinds (`app/brain/memory.py`): working (session
turns), episodic (turn log plus outcome counters), semantic (distilled facts
stored and recalled by key and by search), procedural (the skill manifests).
Session summaries are computed, not hidden. Rejected: one undifferentiated
vector bucket for everything, which makes recall unauditable.

## 6. Orchestration Patterns

Chosen: Anthropic's workflow patterns composed: routing (skill picking),
prompt chaining (skill step lists), evaluator optimizer (draft loop), plus
the harness loop above. Python computes, TypeScript orchestrates product
integrations, the brain plans. Rejected: a single autonomous agent with all
tools and a giant system prompt.

## 7. Guardrails and Permissions

Chosen: layered containment aligned with OWASP LLM Top 10 2025: prompt
injection shield that strips approval proposals from flagged runs, claim
guardrails on every draft, run budgets, PII redaction before memory writes,
permission scopes (read and compute free; write and external are proposals
only), API key auth, roles, and rate limits at the boundary.
Rejected: relying on the model to police itself.

## 8. Evals for Agents

Chosen: a golden dataset for the domain plus harness level cases (shield
blocking, budget rejection) in `services/engine-py/evals/`, run in CI on
every change, with the rule that every real failure becomes a new case.
Rejected: demo based confidence and LLM judge only scoring with no ground
truth set.

## 9. Human in the Loop Design

Chosen: approvals as first class, enriched objects: tool, risk level, scope,
a human readable preview, and a 30 minute expiry, decided in the TypeScript
gate (pending, approved, rejected, expired; nothing skippable). Detractors
and lapsed customers are human first by playbook, not by automation.
Rejected: approve everything buttons and silent auto sends.

## 10. Observability and Tracing

Chosen: correlation ids on every HTTP request and response, per route
metrics at /metrics, per skill outcome counters in memory insights, and full
span traces per brain run at /v1/brain/traces (phase, tool, retry, guard,
with timings and statuses). Rejected: print debugging and after the fact log
archaeology.
