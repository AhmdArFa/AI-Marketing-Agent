# AI Marketing Agent

An AI marketing agent with a real brain, built for one domain first:
**automotive ERP, the 4S PLUS product by Vo Technology** (Sales, Spare Parts,
Service, Survey). It scores prospects, builds retention campaigns from live
service data, plans content from domain pillars, and checks every claim it
makes, while a human approves anything that touches the outside world.

Built as a proof of concept for Vo Technology first, structured so it can be
packaged for other companies and other domains later.

## Why it is built this way

- **TypeScript owns orchestration and product.** Intent routing, OAuth tools,
  sessions, streaming, and the human approval gate.
- **Python owns data, models, and the brain.** Pandas analytics, retrieval,
  lead scoring, segmentation, planning, and structured inference in a
  stateless FastAPI service.
- **The brain plans with tools and skills.** A goal goes in; the brain recalls
  memory, picks a skill from declarative manifests, runs compute tools, passes
  drafts through claim guardrails, and returns mutations only as pending
  approvals. It has no code path that sends or publishes anything.
- **Numbers come from code, never from a model.** CPA, ROAS, lead scores, and
  segments are pure, tested functions. Models write language only.

Architecture and patterns: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Security model: [docs/SECURITY.md](docs/SECURITY.md).
Domain pack structure: [docs/domain-4splus/DOMAIN_PACK.md](docs/domain-4splus/DOMAIN_PACK.md).

## What works now

Python engine (`services/engine-py`):

- Brain: `POST /v1/brain/run`, plus `GET /v1/brain/skills` and `/v1/brain/tools`
  catalogs (the tools catalog also renders in MCP format with
  `?format=mcp`). Seven skills loaded: prospect lead scoring, dealer
  retention, campaign analysis and draft, monthly content calendar, campaign
  brief builder, draft guardrail review, daily briefing.
- Draft quality: an evaluator optimizer loop scores drafts on guardrail
  compliance, call to action, length, and grounding, then revises and rescores.
- Defenses aligned with the OWASP LLM Top 10 (2025): a prompt injection
  shield that blocks approval proposals on flagged runs, per run budgets,
  PII redaction before memory storage. See [docs/SECURITY.md](docs/SECURITY.md).
- Evaluation: a golden dataset for the domain in `services/engine-py/evals/`
  runs in CI, so retrieval, scoring, segmentation, and guardrail quality
  cannot silently regress. The research behind this round:
  [docs/RESEARCH_NOTES.md](docs/RESEARCH_NOTES.md).
- Observability: correlation IDs on every response and per route counters at
  `GET /metrics`.
- Domain pack for 4S PLUS: explainable lead scoring, retention segments
  (maintenance due, lapsed winback, survey detractors and promoters), pillar
  content calendar, claim guardrails, all grounded in verified product facts
  such as the JobCard lifecycle (W.I.P to Ready for invoicing) and the One Car
  Journey by chassis number.
- Analytics: Pandas campaign performance (CTR, CPC, CPA, ROAS).
- Retrieval: brand, personal, and domain knowledge collections.
- Security middleware: API key auth with role checks on writes, rate
  limiting, body size cap, security headers.

TypeScript orchestrator (`apps/orchestrator-ts`):

- Intent router in English and Arabic, Zod contracts mirrored from Pydantic,
  config validated at startup, hardened engine client (timeout, one retry,
  API key header), approval gate state machine, and 4S PLUS workflows.

## Run it

```bash
# Python engine
cd services/engine-py
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
pytest -q

# TypeScript orchestrator (new terminal)
cd apps/orchestrator-ts
npm install
npm run demo
```

Or with Docker: copy `.env.example` to `.env`, then `docker compose up --build`.

Try the brain:

```bash
curl -X POST http://localhost:8000/v1/brain/run \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","goal":"Score my dealer leads and follow up","context":{"leads":[{"company":"Delta Motors","business_type":"dealer","branches":3,"monthly_jobs_or_sales":240,"current_system":"excel","signals":["demo_requested"],"days_since_last_touch":2}]}}'
```

## LLM providers

Provider agnostic by design: Gemini primary (Arabic strength, long context),
OpenAI as the structured output fallback, Anthropic for long form copy, and
Ollama with Qwen for sovereign, fully offline tenants. Mock mode is the
default, so the whole system runs and tests pass with no keys at all.

## Roadmap

1. Live Gmail and Google Calendar adapters in TypeScript.
2. Chroma for local vectors, pgvector in production, same interface.
3. LangGraph.js graphs for multi step campaigns with resumable approvals.
4. Next.js product UI with streaming.
5. LLM planner strategy behind the current planner interface.
6. Package per tenant: one domain pack, one skill set, one approval policy.

## License

MIT. See [LICENSE](LICENSE).
