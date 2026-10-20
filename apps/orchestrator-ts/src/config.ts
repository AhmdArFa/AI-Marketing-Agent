import { z } from "zod";

// Fail fast on bad configuration. Every environment value the orchestrator
// depends on is parsed here, once, at startup. No scattered process.env reads.
const EnvSchema = z.object({
  PYTHON_ENGINE_URL: z.string().url().default("http://localhost:8000"),
  ENGINE_API_KEY: z.string().optional(),
  ENGINE_TIMEOUT_MS: z.coerce.number().int().positive().default(15000),
});

export const config = EnvSchema.parse(process.env);
