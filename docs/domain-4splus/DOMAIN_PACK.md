# 4S PLUS Domain Pack: Structure

This pack turns the generic hybrid agent into a marketing agent for one
specific domain: automotive ERP, the 4S PLUS product by Vo Technology.
The generic layers never change. All domain specificity lives here, so the
pack can improve on its own schedule and can be re-skinned for another
vertical later by swapping the pack, not the engine.

## The two audiences (never mix them)

1. **Prospecting (B2B):** Vo Technology marketing 4S PLUS to dealer owners,
   workshop managers, and parts traders. Goal: qualified demo bookings.
2. **Dealer marketing (B2C):** a dealer using 4S PLUS service and survey data
   to retain car owners. Goal: booked maintenance appointments and recovered
   detractors. This is both a product feature and the proof story for audience 1.

## Pack layout

```text
services/engine-py/app/domain4s/
  catalog.py          product facts, personas, pillars, prohibited claims
  schemas.py          ProspectLead, VehicleServiceRecord, calendar, guardrails
  lead_scoring.py     explainable prospect scoring (from the CRM AI deck)
  retention.py        maintenance due, lapsed, detractor, promoter segments
  content_calendar.py pillar rotation calendar (Marwa Nasr operating system)
  guardrails.py       prohibited claims and unverified percentage checks
docs/domain-4splus/
  DOMAIN_PACK.md      this file
  playbooks/          one file per campaign playbook
apps/orchestrator-ts/src/agents/marketing4s.ts
                      TypeScript workflows calling the pack, approval gated
```

## Data triggers, straight from the real system

| 4S PLUS source | Field or event | Marketing trigger |
| :--- | :--- | :--- |
| Periodic Maintenance Service | months or km since last service | maintenance due segment |
| Survey after delivery | score 0 to 10 | 6 or less triggers detractor recovery, 9 or more triggers the promoter playbook |
| JobCard | status W.I.P or Ready for invoicing | customer excluded from campaigns while a card is open |
| Sales | chassis number on a sold car | full history and warranty story in every later campaign |
| Spare Parts | Create Requests and Issues flow | parts availability angle in service package offers |
| CRM | lead signals and follow ups | prospect scoring tiers and next actions |

## How to improve the pack (extension points)

1. **New fact:** add it to `catalog.py` and as a RAG seed document. Nothing else changes.
2. **New persona:** add to `PROSPECT_PERSONAS` or `RETAIL_PERSONAS` with pains and a trigger moment.
3. **New playbook:** one markdown file in `playbooks/`, one segment rule in `retention.py` or one scoring signal in `lead_scoring.py`, one test.
4. **Better scoring:** replace rule weights in `lead_scoring.py` with a trained model behind the same request and response schemas.
5. **New channel:** implement it in TypeScript tools only. Python never sends.
6. **Stricter claims:** extend `PROHIBITED_CLAIMS`. The guardrail endpoint picks it up immediately.

## Improvement loop

Monthly, following the content operating system already adopted:
measure playbook results (demo bookings, appointments booked, detractors
recovered), write the insights into `catalog.py` facts and playbook files,
adjust scoring weights and pillar rotation, ship the pack as a new version.
The generic engine and orchestrator are not touched in this loop.
