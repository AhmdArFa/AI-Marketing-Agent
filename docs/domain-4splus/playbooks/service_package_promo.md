# Playbook: Service Package Promo and Lapsed Winback

Audience: dealer marketing. Sources: Service Packages menu, Discount On
Labour and Parts settings, lapsed segment (two intervals or more overdue).

Steps:
1. Python builds the lapsed_winback segment. These customers get a human call
   first, not a broadcast.
2. The call offers a defined Service Package with its real contents and real
   prices from the system. The agent drafts the script and the follow up
   message, both approval gated.
3. Maintenance due customers (not yet lapsed) may receive the package inside
   the periodic reminder instead, approval gated as a batch.

KPI: winback rate, package attach rate, average JobCard value trend.
Guardrail: prices and discounts come only from the system's own settings,
never invented by the agent. If a price is missing, the draft is parked and
the missing field is reported.
