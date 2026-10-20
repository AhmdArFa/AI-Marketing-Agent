// Human in the loop approval gate.
// Rule: any mutating tool (send, publish, create event) is queued here first.
// Nothing executes until approve(id) is called with the user's decision.

export interface PendingApproval {
  id: string;
  tool: string;
  payload: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
}

export class ApprovalGate {
  private queue: PendingApproval[] = [];
  private seq = 0;

  enqueue(tool: string, payload: Record<string, unknown>): PendingApproval {
    const item: PendingApproval = {
      id: `approval-${++this.seq}`,
      tool,
      payload,
      status: "pending",
    };
    this.queue.push(item);
    return item;
  }

  decide(id: string, approved: boolean): PendingApproval {
    const item = this.queue.find((q) => q.id === id);
    if (!item) throw new Error(`Unknown approval id: ${id}`);
    item.status = approved ? "approved" : "rejected";
    return item;
  }

  pending(): PendingApproval[] {
    return this.queue.filter((q) => q.status === "pending");
  }

  all(): PendingApproval[] {
    return [...this.queue];
  }
}
