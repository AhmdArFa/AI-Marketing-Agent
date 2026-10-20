// Static catalog data for the explorers. Source of truth is the codebase
// itself: every entry names the real file that implements it.

export interface Layer {
  id: string;
  name: string;
  stack: string;
  owns: string[];
  files: string[];
  color: string;
}

export const LAYERS: Layer[] = [
  {
    id: "product",
    name: "Product and Orchestration",
    stack: "TypeScript, Next.js, Node",
    owns: ["Intent routing", "OAuth tools (Gmail, Calendar, social)", "Human approval gate", "Sessions and streaming UI"],
    files: ["apps/orchestrator-ts/src/agents/router.ts", "apps/orchestrator-ts/src/tools/approval.ts", "apps/web (this UI)"],
    color: "#f59e0b",
  },
  {
    id: "contract",
    name: "Contract Boundary",
    stack: "REST, OpenAPI, Pydantic v2 mirrored in Zod",
    owns: ["Type safety between runtimes", "Request and response validation in both directions", "Versioned /v1 endpoints"],
    files: ["services/engine-py/app/schemas.py", "apps/orchestrator-ts/src/contracts.ts"],
    color: "#38bdf8",
  },
  {
    id: "brain",
    name: "Agent Brain",
    stack: "Python, planner, tool registry, skill manifests",
    owns: ["Perceive, plan, act, guard, reflect loop", "Skill selection with explicit plans", "Memory: episodic, semantic, procedural", "Evaluator optimizer for drafts", "Prompt injection shield and run budgets"],
    files: ["services/engine-py/app/brain/brain.py", "services/engine-py/app/brain/planner.py", "services/engine-py/app/brain/skills/*.json"],
    color: "#a78bfa",
  },
  {
    id: "data",
    name: "Data and Model",
    stack: "Python, FastAPI, Pandas, TF IDF to Chroma and pgvector",
    owns: ["Campaign analytics (numbers from code, never from a model)", "RAG over brand, personal, and domain knowledge", "Lead scoring and retention segmentation", "Provider agnostic LLM inference"],
    files: ["services/engine-py/app/pipelines/marketing_analytics.py", "services/engine-py/app/domain4s/lead_scoring.py", "services/engine-py/app/models/llm_client.py"],
    color: "#34d399",
  },
];

export interface Pattern {
  name: string;
  kind: "Design" | "Architecture" | "Agent";
  where: string;
  why: string;
}

export const PATTERNS: Pattern[] = [
  { name: "Registry", kind: "Design", where: "app/brain/tools_registry.py", why: "Tools are named, described, and flagged for mutation and approval in one place. Discovery beats wiring." },
  { name: "Strategy", kind: "Design", where: "app/brain/planner.py, app/models/llm_client.py", why: "Planner and LLM provider swap behind one interface: deterministic today, model driven tomorrow, Gemini or Ollama per tenant." },
  { name: "Repository", kind: "Design", where: "app/brain/memory.py, app/pipelines/rag.py", why: "Memory and knowledge hide storage behind recall and search, so TF IDF can become Chroma or pgvector without caller changes." },
  { name: "Factory", kind: "Design", where: "build_default_registry()", why: "One assembly point for the tool set keeps configuration honest and testable." },
  { name: "Chain of Responsibility", kind: "Design", where: "app/security.py middleware", why: "Rate limit, size cap, auth, role check, and headers run in a fixed order before any business logic." },
  { name: "State Machine", kind: "Design", where: "apps/orchestrator-ts/src/tools/approval.ts", why: "Approvals move pending to approved or rejected. No state can be skipped, so no mutation can slip through." },
  { name: "Adapter", kind: "Design", where: "apps/orchestrator-ts/src/clients/pythonEngine.ts", why: "The Zod checked client adapts the Python contract to TypeScript, with timeout and a single bounded retry." },
  { name: "Hexagonal (Ports and Adapters)", kind: "Architecture", where: "Whole repo layout", why: "Domain core depends on nothing external. HTTP, SaaS APIs, and vector stores are adapters at the edges." },
  { name: "Clean Architecture", kind: "Architecture", where: "domain4s rules inside, API outside", why: "Scoring and segmentation are pure functions. Frameworks and transport never leak into the domain." },
  { name: "Routing (agent pattern)", kind: "Agent", where: "Planner skill picking", why: "Anthropic workflow pattern: classify the goal, send it down a specialized path instead of one giant prompt." },
  { name: "Prompt Chaining (agent pattern)", kind: "Agent", where: "Skill manifests steps", why: "Each skill is a fixed, inspectable chain of tool steps with gates between them." },
  { name: "Evaluator Optimizer (agent pattern)", kind: "Agent", where: "app/brain/evaluator.py", why: "Drafts are scored on explicit criteria, revised, and rescored in a bounded loop. Quality is measured, not hoped for." },
  { name: "Declarative Skills", kind: "Agent", where: "app/brain/skills/*.json", why: "Capabilities are data: triggers, steps, follow up tool, guardrails. Adding a skill needs no brain code change." },
];

export const PRINCIPLES: { name: string; how: string }[] = [
  { name: "Simplicity first", how: "Anthropic's core lesson: add complexity only when it demonstrably improves outcomes. The planner is deterministic on purpose." },
  { name: "Transparency", how: "Every run shows its plan, its steps, its scores, and its blocked actions. Nothing is a black box." },
  { name: "Single Responsibility", how: "Python computes, TypeScript orchestrates and acts, the brain plans. Layers never leak into each other." },
  { name: "Open for extension", how: "New tool, new skill manifest, new domain pack: extension without modifying the core." },
  { name: "Numbers from code, never from a model", how: "CPA, ROAS, lead scores, and segments are pure tested functions. Models write language only." },
  { name: "Security by design", how: "OWASP LLM 2025 mapping: injection containment, least agency, budgets, PII redaction, auth and roles at the boundary." },
  { name: "Human in the loop", how: "The brain has no mutation code path. Every send, publish, or booking waits for a human decision." },
  { name: "Never invent, report missing", how: "When a brief field or a price is missing, the system parks the work and says what is missing." },
  { name: "Evaluate everything", how: "A golden dataset for the domain runs in CI. Quality regressions fail the build like any other bug." },
];

export const BRAIN_LOOP = [
  { step: "Perceive", detail: "Recall relevant memory and knowledge for the goal" },
  { step: "Plan", detail: "Pick a skill, emit an explicit step by step plan" },
  { step: "Act", detail: "Run compute tools only. Mutations become proposals" },
  { step: "Guard", detail: "Claim guardrails, draft evaluation, injection shield" },
  { step: "Reflect", detail: "Log the turn and per skill outcome counters" },
];

export const MODULES = [
  { name: "Sales", owner: "Ahmed Fouad", facts: "Vehicle inventory by model, color, chassis, and status. A sold car's chassis carries its full history into Service." },
  { name: "Spare Parts", owner: "Hazem", facts: "Create Requests from the JobCard, Confirm, Issues: stock drops instantly. Bulk load from Excel." },
  { name: "Service", owner: "Ahmed Gamal", facts: "JobCard lifecycle W.I.P to Ready for invoicing. Actual versus Sold hours. Packages, periodic maintenance, appointments, QC checklist, Follow Customer." },
  { name: "Survey", owner: "Product pillar", facts: "Satisfaction surveyed after delivery. Scores drive detractor recovery and promoter referral playbooks." },
  { name: "CRM", owner: "Shahd", facts: "Customer files, follow ups, reminders, marketing. AI layer adds lead scoring, automation, and predictive insights." },
  { name: "Accounting", owner: "Ibrahim", facts: "Invoices at Ready for invoicing. Actual versus Sold hours feed per JobCard profitability." },
];

export const JOURNEY = ["Sold in Sales, chassis recorded", "JobCard opens in Service with full history", "Parts requested and issued from stock", "Ready for invoicing, profit known per card", "CRM survey and next maintenance alert", "Feedback feeds the next campaign"];

export const PERSONAS = [
  { title: "Dealer or showroom owner", audience: "Prospecting (B2B)", pains: "Lost customer data, no single view of sales and service, follow ups by memory" },
  { title: "Workshop manager", audience: "Prospecting (B2B)", pains: "No technician efficiency view, paper job cards, parts shortages mid job" },
  { title: "Parts trader", audience: "Prospecting (B2B)", pains: "Unclear stock, no demand signal from the workshop, dead stock" },
  { title: "Car owner due for maintenance", audience: "Dealer marketing (B2C)", pains: "Forgets intervals, fears surprise costs, loses service history at resale" },
  { title: "Survey detractor", audience: "Dealer marketing (B2C)", pains: "Feels unheard after a bad visit. Human call first, never an automated offer" },
];

export const PLAYBOOKS = [
  { name: "Periodic Maintenance Reminder", trigger: "Months or km reach the service interval, no open JobCard", channel: "WhatsApp, then call", kpi: "Appointments booked per 100 reminders" },
  { name: "Detractor Recovery", trigger: "Survey score 6 or less", channel: "Human call only", kpi: "Recovery rate, contact within 24 hours" },
  { name: "Promoter Review and Referral", trigger: "Survey score 9 or 10", channel: "WhatsApp", kpi: "Reviews and referrals collected" },
  { name: "Service Package Winback", trigger: "Two or more intervals overdue", channel: "Call first, package from real system prices", kpi: "Winback rate, package attach rate" },
  { name: "Dealer Prospect Demo Campaign", trigger: "Lead tier hot or warm from scoring", channel: "Follow up task, approval gated", kpi: "Demos booked per 100 leads" },
];
