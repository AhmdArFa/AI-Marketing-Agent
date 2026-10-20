# Architecture

## Design principles

1. **Clean architecture.** The domain (4S PLUS catalog, scoring rules, retention
   rules, guardrails) depends on nothing external. Pipelines depend on the
   domain. The API depends on pipelines and the brain. Adapters (HTTP clients,
   vector stores, LLM providers) sit at the edges and can be swapped.
2. **Hexagonal, ports and adapters.** TypeScript talks to Python only through
   the versioned HTTP contract. Python never calls SaaS APIs. OAuth and side
   effects are TypeScript ports with swappable adapters.
3. **Single responsibility per layer.** Python computes. TypeScript
   orchestrates and performs side effects. The brain plans.
4. **Explicit over implicit.** Plans, tool contracts, skill manifests, and
   approval states are data you can read, test, and diff in review.
5. **Deterministic where it matters.** Money math (CPA, ROAS), scoring, and
   segmentation are pure functions with tests. Models write language, never
   numbers.

## Patterns in use

| Pattern | Where | Why |
| :--- | :--- | :--- |
| Registry | `brain/tools_registry.py` | Tools are named, described, and tagged with mutation and approval flags |
| Strategy | `brain/planner.py`, `models/llm_client.py` | Planner and LLM provider are replaceable behind one interface |
| Repository | `brain/memory.py`, `pipelines/rag.py` | Memory and knowledge hide their storage behind recall and search methods |
| Chain of responsibility | `security.py` middleware | Rate limit, size cap, auth, role check, headers, in order |
| State machine | `tools/approval.ts` | Approvals move pending to approved or rejected, nothing skips a state |
| Factory | `tools_registry.build_default_registry` | One place assembles the tool set |
| Adapter | `clients/pythonEngine.ts` | Zod checked boundary between two runtimes |
| Declarative skills | `brain/skills/*.json` | Capabilities are data, reviewed like code, added without touching the brain |

## The brain loop

Perceive (memory recall) to Plan (skill match, explicit steps) to Act
(compute tools only) to Guard (claim checks on drafts) to Reflect (turn log
and per skill outcome counters). Mutations are proposals, and the loop has
no code path that executes one.

## Extension points

- New tool: register it, tag it, test its handler.
- New skill: drop a JSON manifest in `brain/skills/`.
- New domain: add a pack beside `domain4s/` and its playbooks under `docs/`.
- New LLM provider: extend the strategy in `models/llm_client.py`.
- New channel: implement the TypeScript tool interface, keep approval gating.
