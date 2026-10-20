import { z } from "zod";

// Zod mirrors of the Python Pydantic v2 schemas in services/engine-py/app/schemas.py.
// Any payload crossing the TypeScript boundary is parsed here first.

export const DomainSchema = z.enum(["marketing", "personal"]);
export type Domain = z.infer<typeof DomainSchema>;

export const InferenceRequestSchema = z.object({
  domain: DomainSchema,
  task_type: z.string().min(1),
  user_query: z.string().min(1),
  context_data: z.record(z.unknown()).default({}),
  brand_voice_id: z.string().optional(),
});
export type InferenceRequest = z.infer<typeof InferenceRequestSchema>;

export const ActionItemSchema = z.object({
  title: z.string(),
  priority: z.enum(["high", "medium", "low"]),
  due_window: z.string().optional().nullable(),
  suggested_tool: z.string().optional().nullable(),
  payload: z.record(z.unknown()).default({}),
});
export type ActionItem = z.infer<typeof ActionItemSchema>;

export const InferenceResponseSchema = z.object({
  summary: z.string(),
  structured_output: z.record(z.unknown()),
  recommended_actions: z.array(ActionItemSchema),
  grounding_sources: z.array(z.string()),
});
export type InferenceResponse = z.infer<typeof InferenceResponseSchema>;
