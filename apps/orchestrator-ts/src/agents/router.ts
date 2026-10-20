import { PythonEngineClient } from "../clients/pythonEngine.js";
import { Domain, InferenceResponse } from "../contracts.js";
import { ApprovalGate, PendingApproval } from "../tools/approval.js";
import { demoMarketingTools, MarketingTools } from "../tools/marketingApis.js";
import { demoWorkspaceTools, WorkspaceTools } from "../tools/workspace.js";
import { classifyMarketingTask, gatherMarketingContext } from "./marketing.js";
import { classifyPersonalTask, gatherPersonalContext } from "./personal.js";

export interface AgentTaskInput {
  userId: string;
  prompt: string;
  explicitDomain?: Domain;
  requireApprovalForMutations?: boolean;
}

export interface OrchestratorResult {
  routedDomain: Domain;
  taskType: string;
  engineResult: InferenceResponse;
  executedTools: string[];
  pendingApprovals: PendingApproval[];
}

const MARKETING_TERMS = [
  "campaign", "seo", "ad ", "ads", "copy", "ctr", "roas", "social", "newsletter",
  "brand", "funnel", "marketing", "حملة", "تسويق", "اعلان", "إعلان",
];
const PERSONAL_TERMS = [
  "email", "inbox", "calendar", "schedule", "briefing", "my day", "بريد", "موعد", "يومي",
];

export function classifyIntent(
  prompt: string,
  explicitDomain?: Domain,
): { domain: Domain; taskType: string } {
  if (explicitDomain) {
    return {
      domain: explicitDomain,
      taskType:
        explicitDomain === "marketing"
          ? classifyMarketingTask(prompt)
          : classifyPersonalTask(prompt),
    };
  }
  const lower = ` ${prompt.toLowerCase()} `;
  const mScore = MARKETING_TERMS.filter((t) => lower.includes(t)).length;
  const pScore = PERSONAL_TERMS.filter((t) => lower.includes(t)).length;
  const domain: Domain = mScore >= pScore && mScore > 0 ? "marketing" : pScore > 0 ? "personal" : "personal";
  return {
    domain,
    taskType: domain === "marketing" ? classifyMarketingTask(prompt) : classifyPersonalTask(prompt),
  };
}

export class HybridAgentOrchestrator {
  readonly approvals = new ApprovalGate();

  constructor(
    private readonly engine = new PythonEngineClient(),
    private readonly marketingTools: MarketingTools = demoMarketingTools,
    private readonly workspaceTools: WorkspaceTools = demoWorkspaceTools,
  ) {}

  async handleUserTask(input: AgentTaskInput): Promise<OrchestratorResult> {
    const { domain, taskType } = classifyIntent(input.prompt, input.explicitDomain);

    // 1. TypeScript gathers live context (OAuth tools live here only).
    const contextData =
      domain === "marketing"
        ? await gatherMarketingContext(this.marketingTools, input.userId)
        : await gatherPersonalContext(this.workspaceTools, input.userId);

    // 2. Python does data, retrieval, and model work. Stateless, no side effects.
    const engineResult = await this.engine.executePipeline({
      domain,
      task_type: taskType,
      user_query: input.prompt,
      context_data: contextData,
      brand_voice_id: domain === "marketing" ? "growth-b2b-v1" : undefined,
    });

    // 3. Every recommended mutation goes to the approval gate first.
    const executedTools: string[] = [];
    const pendingApprovals: PendingApproval[] = [];
    const requireApproval = input.requireApprovalForMutations ?? true;
    for (const action of engineResult.recommended_actions) {
      if (!action.suggested_tool) continue;
      if (requireApproval) {
        pendingApprovals.push(this.approvals.enqueue(action.suggested_tool, action.payload));
      } else {
        executedTools.push(action.suggested_tool);
      }
    }

    return { routedDomain: domain, taskType, engineResult, executedTools, pendingApprovals };
  }
}
