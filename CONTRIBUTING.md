# Contributing

## Rules that keep this codebase clean

1. Domain logic is pure and tested. No network, no file system, no clock reads
   inside `domain4s/` rules or analytics pipelines.
2. New capability means: a tool registration, a skill manifest, and a test.
   If it mutates anything, it also goes through the approval gate.
3. Numbers come from code, never from a model. Drafts that mention numbers
   must pass the guardrail check.
4. Secrets never enter the repo. Use `.env` locally, environment variables in
   deployment.
5. Keep the layers honest: Python computes, TypeScript orchestrates and acts,
   the brain plans. Do not leak responsibilities across layers.

## Local checks before a pull request

```bash
cd services/engine-py && pytest -q
cd apps/orchestrator-ts && npm run typecheck
```

CI runs the same checks on every push.
