# Research Notes: v0.3 Improvement Round

Studied on 2026-10-20 before writing the v0.3 code. Each finding maps to a
concrete change in this repository, listed at the end of its section.

## 1. Agent workflow patterns (Anthropic)

Source: [Building Effective Agents, Anthropic Engineering](https://www.anthropic.com/engineering/building-effective-agents)

The most successful production systems use simple, composable patterns:
prompt chaining, routing, parallelization, orchestrator workers, and
evaluator optimizer. Three principles: keep the design simple, make planning
steps transparent, and treat tools as a carefully documented interface.
Workflows with predefined code paths beat open ended autonomy when the task
shape is known, which is exactly the marketing case.

Where we stood: routing (skill picking) and chaining (skill steps) existed.
Missing: the evaluator optimizer loop for copy quality.

Change shipped: a deterministic draft evaluator with an optimize loop in
`app/brain/evaluator.py`. Drafts are scored on guardrail compliance, call to
action presence, length discipline, and grounding, then revised and rescored
for a bounded number of iterations, with every score kept in the run result.

## 2. LLM security risks (OWASP Top 10 for LLM Applications, 2025)

Sources: [OWASP LLM Top 10 2025 summary, BSG](https://bsg.tech/blog/owasp-llm-top-10/), [controls per risk](https://fixthevuln.com/owasp-llm-top10.html)

The 2025 list: prompt injection (LLM01), sensitive information disclosure
(LLM02), supply chain (LLM03), data and model poisoning (LLM04), improper
output handling (LLM05), excessive agency (LLM06), system prompt leakage
(LLM07), vector and embedding weaknesses (LLM08), misinformation (LLM09), and
unbounded consumption (LLM10). OWASP is explicit that prompt injection has no
foolproof prevention, so the design goal is containment: least privilege,
separation of trusted instructions from untrusted content, and human approval
for high impact actions.

Where we stood: excessive agency was already contained by the approval gate,
and rate limiting covered part of consumption.

Changes shipped:
- Injection shield in `app/brain/shield.py`: goals and context text are
  scanned for known injection patterns. Flagged runs still compute, but the
  flag is recorded, drafts are blocked from approval proposals, and the event
  lands in memory insights (containment, not a false promise of prevention).
- Run budget: the brain caps plan steps and total context size per run,
  returning a clear error when exceeded (LLM10).
- PII redaction in `app/brain/shield.py`: emails and phone numbers in
  free text fields are masked before anything is stored in memory (LLM02).
- The full control mapping lives in `docs/SECURITY.md`.

## 3. Evaluation: golden datasets and RAG metrics

Sources: [RAG evaluation metrics, Sphere](https://sphereinc.com/blogs/rag-evaluation-metrics), [production LLM evals tutorial](https://acethecloud.com/blog/production-llm-systems-evaluation-ab-testing/)

Practice that works: a golden dataset of questions with known good answers
and supporting documents, retrieval scored separately from generation
(recall at K, MRR), faithfulness as the hallucination metric, evals run in CI
on every pipeline change, and every real failure becoming a new golden case.

Changes shipped: `evals/golden.jsonl` with retrieval, scoring, segmentation,
and guardrail cases for the 4S PLUS domain, a runner in `evals/run_evals.py`
that reports hit rate at K and case pass rate, and a pytest wrapper so CI
fails when quality regresses.

## 4. Agent memory types

Sources: [agent memory types and best practices](https://47billion.com/blog/ai-agent-memory-types-implementation-best-practices/), [long term memory implementation](https://atlan.com/know/how-to-implement-long-term-memory-ai-agents/)

Production memory splits into working (session), episodic (what happened),
semantic (facts and preferences), and procedural (how to behave, which for us
is the skill manifests). Scope isolation by user, agent, and session matters
as much as the store.

Changes shipped: `AgentMemory` now keeps the three kinds explicitly: episodic
turns per session (existing), semantic facts the agent can store and recall
by key through `remember_fact` and `recall_facts`, and procedural memory
documented as the skill manifests it already loads. Fact storage goes through
the same retrieval repository, no second store to operate.

## 5. Tool interoperability (MCP)

Source: [Model Context Protocol overview](https://metavert.io/model-context-protocol)

MCP is the ecosystem standard for tool discovery: servers publish tools with
names, descriptions, and JSON input schemas, and any compatible client can
enumerate them. Tools are the broadly supported capability; resources and
prompts have thinner support, so tools first is the right bet.

Change shipped: the tool catalog endpoint can render the registry in MCP
tools format (`GET /v1/brain/tools?format=mcp`), each tool carrying an
`inputSchema`. The registry stays the single source of truth, so an MCP
server facade can be added later without touching tool code.

## 6. What leading marketing agents ship

Source: [best AI agents for marketing, 2026 roundup](https://www.wix.com/blog/best-ai-agents-for-marketing)

The category leaders (HubSpot Breeze, Salesforce Agentforce) converge on:
specialized agents per job (prospecting, content, nurture), buying signal
detection feeding lead scoring, campaign planning from a brief instead of a
blank prompt, content grounded in brand voice, and governance views showing
which agents ran and what they touched, with pause rules when an account
needs a human first.

Changes shipped:
- New buying signals in lead scoring: `demo_attended` and
  `case_study_download`, weighted between a reply and a demo request.
- A campaign brief builder: `app/domain4s/campaign_brief.py` plus the
  `campaign_brief_builder` skill and `/v1/domain4s/campaign-brief` endpoint,
  turning brief answers into audiences, pillars, cadence, and KPIs, following
  the brief first rule from our own content strategy template.
- Governance: correlation IDs on every request and a `/metrics` endpoint
  with per route counters, so runs are auditable (see also section 2).
