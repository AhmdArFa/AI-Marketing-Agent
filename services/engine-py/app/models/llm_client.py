"""Provider agnostic LLM client.

Routing (best case):
  gemini    primary, Arabic strength, long context, triage volume
  openai    fallback when strict structured output validation fails
  anthropic long form copy (SEO, blog)
  ollama    sovereign offline mode for personal and sensitive data
  mock      deterministic, default when no key is configured, used in tests

The client returns plain dicts. Callers validate them with Pydantic schemas,
so a bad model output never leaks downstream unchecked.
"""

import os
from typing import Any, Dict


class LLMClient:
    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()

    def draft_copy(self, query: str, grounding: list[str], brand_voice_id: str | None) -> str:
        voice = brand_voice_id or "default"
        base = f"Draft for: {query}. Voice: {voice}."
        if grounding:
            base += f" Grounded in {len(grounding)} retrieved source(s), no invented claims."
        if self.provider == "mock":
            return base + " [mock provider: connect Gemini, OpenAI, Anthropic, or Ollama for live generation]"
        return base + f" [provider: {self.provider}, live call to be wired with its SDK]"

    def summarize(self, title: str, items: list[Dict[str, Any]]) -> str:
        if self.provider == "mock":
            return f"{title}: {len(items)} item(s) processed deterministically in mock mode."
        return f"{title}: {len(items)} item(s). [provider: {self.provider}]"
