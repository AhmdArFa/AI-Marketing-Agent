import { FourSMarketingWorkflows } from "./agents/marketing4s.js";
import { HybridAgentOrchestrator } from "./agents/router.js";

// Demo entrypoint. Run the Python engine first:
//   uvicorn app.main:app --port 8000   (from services/engine-py)
// Then: npm run demo
async function main() {
  const agent = new HybridAgentOrchestrator();

  const marketing = await agent.handleUserTask({
    userId: "ahmed",
    prompt: "Analyze my campaign ROAS and draft a social post about the results",
  });
  console.log("MARKETING:", marketing.routedDomain, marketing.taskType);
  console.log(" summary:", marketing.engineResult.summary);
  console.log(" pending approvals:", marketing.pendingApprovals.map((a) => `${a.id} -> ${a.tool}`));

  const personal = await agent.handleUserTask({
    userId: "ahmed",
    prompt: "Give me my daily briefing for today",
  });
  console.log("PERSONAL:", personal.routedDomain, personal.taskType);
  console.log(" summary:", personal.engineResult.summary);
  console.log(" pending approvals:", personal.pendingApprovals.map((a) => `${a.id} -> ${a.tool}`));

  console.log("Executed tools without approval:", [
    ...marketing.executedTools,
    ...personal.executedTools,
  ]);

  const fourS = new FourSMarketingWorkflows();
  const leads = await fourS.scoreProspectLeads([
    {
      company: "Delta Motors",
      business_type: "dealer",
      branches: 3,
      monthly_jobs_or_sales: 240,
      current_system: "excel",
      signals: ["demo_requested", "replied"],
      days_since_last_touch: 2,
    },
  ]);
  console.log("4S LEADS:", leads.scored.map((l) => `${l.company} ${l.score} ${l.tier}`));
  console.log(" 4S pending approvals:", leads.pendingApprovals.map((a) => `${a.id} -> ${a.tool}`));

  const retention = await fourS.buildRetentionCampaign([
    { customer: "Omar", chassis: "CH1", months_since_last_service: 7, km_since_last_service: 4000 },
    { customer: "Karim", chassis: "CH3", months_since_last_service: 1, last_survey_score: 4 },
  ]);
  console.log("4S SEGMENTS:", retention.segments.map((s) => `${s.segment} (${s.customers.length})`));
  console.log(" 4S campaign approvals:", retention.pendingApprovals.map((a) => `${a.id} -> ${a.tool}`));

  const check = await fourS.checkDraft("4S PLUS gives guaranteed results and 40% more sales");
  console.log("4S GUARDRAIL on bad draft:", check.ok, check.violations.length, "violations");

  // The Brain: one goal in, plan and skill and approvals out.
  const { PythonEngineClient } = await import("./clients/pythonEngine.js");
  const brainResult = await new PythonEngineClient().runBrain({
    session_id: "demo",
    goal: "Score my dealer leads and follow up",
    context: {
      leads: [
        {
          company: "Delta Motors",
          business_type: "dealer",
          branches: 3,
          monthly_jobs_or_sales: 240,
          current_system: "excel",
          signals: ["demo_requested", "replied"],
          days_since_last_touch: 2,
        },
      ],
    },
  });
  console.log("BRAIN skill:", brainResult.skill_id);
  console.log(" BRAIN summary:", brainResult.summary);
  console.log(" BRAIN executed mutations:", brainResult.executed_mutations);
}

main().catch((err) => {
  console.error("Demo failed:", err instanceof Error ? err.message : err);
  process.exit(1);
});
