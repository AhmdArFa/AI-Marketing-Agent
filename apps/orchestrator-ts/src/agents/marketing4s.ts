import { z } from "zod";
import { ApprovalGate } from "../tools/approval.js";

// 4S PLUS domain workflows. Python computes, TypeScript orchestrates.
// Every outreach action returns as a pending approval, never auto sent.

const ScoredLeadSchema = z.object({
  company: z.string(),
  score: z.number(),
  tier: z.enum(["hot", "warm", "cold"]),
  reasons: z.array(z.string()),
  next_action: z.string(),
});

const RetentionSegmentSchema = z.object({
  segment: z.string(),
  customers: z.array(z.record(z.unknown())),
  playbook: z.string(),
  channel: z.string(),
  human_first: z.boolean(),
});

async function postJson(baseUrl: string, path: string, body: unknown): Promise<unknown> {
  const r = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`Python Engine error (${r.status}): ${await r.text()}`);
  return r.json();
}

export class FourSMarketingWorkflows {
  constructor(
    private readonly baseUrl: string = process.env.PYTHON_ENGINE_URL ?? "http://localhost:8000",
    private readonly approvals = new ApprovalGate(),
  ) {}

  async scoreProspectLeads(leads: unknown[]) {
    const data = (await postJson(this.baseUrl, "/v1/domain4s/lead-score", { leads })) as {
      scored: unknown[];
      hot_count: number;
    };
    const scored = z.array(ScoredLeadSchema).parse(data.scored);
    // Only hot leads create a human task, and even that is approval gated.
    const pending = scored
      .filter((l) => l.tier === "hot")
      .map((l) =>
        this.approvals.enqueue("crm.createFollowUpTask", {
          company: l.company,
          action: l.next_action,
          score: l.score,
        }),
      );
    return { scored, hotCount: data.hot_count, pendingApprovals: pending };
  }

  async buildRetentionCampaign(records: unknown[]) {
    const data = (await postJson(this.baseUrl, "/v1/domain4s/retention", { records })) as {
      segments: unknown[];
    };
    const segments = z.array(RetentionSegmentSchema).parse(data.segments);
    const pending = segments.map((s) =>
      this.approvals.enqueue(`campaign.prepare:${s.playbook}`, {
        segment: s.segment,
        channel: s.channel,
        humanFirst: s.human_first,
        customerCount: s.customers.length,
      }),
    );
    return { segments, pendingApprovals: pending };
  }

  async buildContentCalendar(weeks = 4, postsPerWeek = 3, audience = "prospecting") {
    const data = (await postJson(this.baseUrl, "/v1/domain4s/content-calendar", {
      weeks,
      posts_per_week: postsPerWeek,
      audience,
    })) as { slots: unknown[] };
    return data.slots;
  }

  async checkDraft(text: string, allowedNumbers: string[] = []) {
    return postJson(this.baseUrl, "/v1/domain4s/guardrails/check", {
      text,
      allowed_numbers: allowedNumbers,
    }) as Promise<{ ok: boolean; violations: string[] }>;
  }
}
