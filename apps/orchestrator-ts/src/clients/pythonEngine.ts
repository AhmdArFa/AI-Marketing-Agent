import { config } from "../config.js";
import {
  InferenceRequest,
  InferenceRequestSchema,
  InferenceResponse,
  InferenceResponseSchema,
} from "../contracts.js";

// Typed client for the Python engine.
// Hardening: per request timeout, one retry on transient failures only,
// API key header when configured, and Zod validation in both directions.
export class PythonEngineClient {
  constructor(private readonly baseUrl: string = config.PYTHON_ENGINE_URL) {}

  private async post(path: string, body: unknown): Promise<unknown> {
    let lastError: unknown;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const response = await fetch(`${this.baseUrl}${path}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(config.ENGINE_API_KEY ? { "X-API-Key": config.ENGINE_API_KEY } : {}),
          },
          body: JSON.stringify(body),
          signal: AbortSignal.timeout(config.ENGINE_TIMEOUT_MS),
        });
        if (response.status >= 500 && attempt === 0) {
          lastError = new Error(`Python Engine error (${response.status})`);
          continue;
        }
        if (!response.ok) {
          throw new Error(`Python Engine error (${response.status}): ${await response.text()}`);
        }
        return await response.json();
      } catch (err) {
        lastError = err;
        if (attempt === 0 && err instanceof TypeError) continue; // transient network error
        throw err;
      }
    }
    throw lastError instanceof Error ? lastError : new Error("Python Engine request failed");
  }

  async executePipeline(payload: InferenceRequest): Promise<InferenceResponse> {
    const checked = InferenceRequestSchema.parse(payload);
    const data = await this.post("/v1/engine/execute", checked);
    return InferenceResponseSchema.parse(data);
  }

  async runBrain(body: {
    session_id: string;
    goal: string;
    context?: Record<string, unknown>;
    explicit_domain?: "marketing" | "personal";
  }): Promise<Record<string, unknown>> {
    return (await this.post("/v1/brain/run", body)) as Record<string, unknown>;
  }

  async health(): Promise<boolean> {
    try {
      const r = await fetch(`${this.baseUrl}/health`, {
        signal: AbortSignal.timeout(3000),
      });
      return r.ok;
    } catch {
      return false;
    }
  }
}
