# Security Model

## Trust boundaries

- The Python engine is a compute service. It is never exposed to end users
  directly in production; the TypeScript orchestrator is the only client.
- The brain can read and compute. It cannot send, publish, book, or write to
  any external system. There is no code path for it: mutating tools exist in
  the registry only as approval proposals.

## Controls implemented

| Threat | Control |
| :--- | :--- |
| Unauthenticated calls to the engine | `X-API-Key` checked in constant time when `ENGINE_API_KEY` is set; `/health` reports whether auth is enabled |
| Privilege abuse on writes | Knowledge ingestion requires an operator or admin role header when auth is enabled |
| Request flooding | Per client sliding window rate limit, 429 with `Retry-After` |
| Giant payload abuse | Body size cap, 413 on violation |
| Browser based attacks on API responses | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` |
| Secret leakage | Keys come from the environment only, are never logged, returned, or committed; `.env` is git ignored |
| Hallucinated marketing claims | Claim guardrails flag prohibited promises and unverified percentages before a human approves anything |
| Prompt injection (OWASP LLM01) | Input shield scans goals and context for injection patterns; flagged runs keep compute results but lose every approval proposal, and the event is recorded. Containment, because OWASP notes there is no foolproof prevention |
| Sensitive data in free text (LLM02) | PII redaction masks emails and phone numbers before text is stored in memory or echoed |
| Unbounded consumption (LLM10) | Per run budgets in the brain (max plan steps, max context size, 413 on excess) on top of the per client rate limit |
| Excessive agency (LLM06) | The brain has no mutation code path at all; mutating tools are approval proposals only, executed by TypeScript after a human decision |
| Unobservable agent behavior | Correlation ID on every request and response, per route metrics at `/metrics`, per skill outcome counters in memory insights |
| Silent automation of outreach | Human in the loop approval gate in TypeScript for every mutation, with an auditable pending state |
| PII overexposure to models | Python receives only the fields a pipeline needs; personal collections are separated from brand collections, and the sovereign Ollama mode keeps sensitive data fully local |

## Production checklist

1. Set a strong `ENGINE_API_KEY` and rotate it on a schedule.
2. Put the engine behind the orchestrator or a private network, never public.
3. Serve everything over HTTPS with a trusted certificate.
4. Use Gemini, OpenAI, or Anthropic only for data you are allowed to send;
   use Ollama mode for sensitive tenants.
5. Back up the knowledge bases and audit approval logs regularly.
6. Review skill manifests and prohibited claims in pull requests like code.

## Reporting

Report vulnerabilities privately to the repository owner. Do not open a
public issue for a security problem.
