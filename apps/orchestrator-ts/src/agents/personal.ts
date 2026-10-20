import { WorkspaceTools } from "../tools/workspace.js";

// Priority order (DECISIONS.md): Gmail and Calendar triage, daily briefing,
// personal document Q&A, Notion and task sync (phase 2).
export async function gatherPersonalContext(tools: WorkspaceTools, userId: string) {
  const [calendar_events, emails] = await Promise.all([
    tools.listTodayEvents(userId),
    tools.listUnreadEmails(userId),
  ]);
  return { calendar_events, emails };
}

export function classifyPersonalTask(prompt: string): string {
  const p = prompt.toLowerCase();
  if (p.includes("triage") || p.includes("inbox") || p.includes("email") || p.includes("بريد")) return "inbox_triage";
  if (p.includes("schedule") || p.includes("calendar") || p.includes("موعد")) return "schedule_optimization";
  return "daily_briefing";
}
