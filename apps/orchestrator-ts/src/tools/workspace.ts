// Personal tool interfaces (OAuth lives here, never in Python).
// Phase 1 wires Gmail and Google Calendar, phase 2 adds Notion and tasks.

export interface CalendarEvent {
  title: string;
  start: string;
}

export interface EmailThread {
  subject: string;
  sender: string;
  snippet?: string;
}

export interface WorkspaceTools {
  listTodayEvents(userId: string): Promise<CalendarEvent[]>;
  listUnreadEmails(userId: string): Promise<EmailThread[]>;
  createFocusBlock(userId: string, start: string, durationMinutes: number): Promise<void>;
}

// Demo implementation with sample data. Replace with Google API clients.
export const demoWorkspaceTools: WorkspaceTools = {
  async listTodayEvents() {
    return [{ title: "Product Sync", start: "11:30" }];
  },
  async listUnreadEmails() {
    return [
      {
        subject: "Urgent: please review the contract",
        sender: "legal@example.com",
        snippet: "Please approve and reply today",
      },
    ];
  },
  async createFocusBlock() {
    throw new Error("Mutating tool: must go through ApprovalGate, never called directly");
  },
};
