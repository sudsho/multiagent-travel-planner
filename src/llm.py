"""provider-agnostic LLM wrapper."""
from __future__ import annotations

import os
from typing import Any, Optional


class LLMResponse:
    def __init__(self, text: str, raw: Any = None):
        self.text = text
        self.raw = raw


class LLM:
    """thin abstraction so agents don't bind directly to a SDK."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Optional[Any] = None

    def _ensure_client(self):
        if self._client is not None:
            return
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"unknown provider: {self.provider}")

    def complete(self, system: str, user: str) -> LLMResponse:
        self._ensure_client()
        if self.provider == "openai":
            res = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return LLMResponse(text=res.choices[0].message.content or "", raw=res)
        # anthropic
        res = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(blk.text for blk in res.content if getattr(blk, "type", None) == "text")
        return LLMResponse(text=text, raw=res)


def llm_from_env(cfg: dict | None = None) -> LLM:
    cfg = cfg or {}
    provider = cfg.get("provider") or os.getenv("LLM_PROVIDER", "openai")
    model = cfg.get("model") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature = float(cfg.get("temperature", 0.3))
    max_tokens = int(cfg.get("max_tokens", 1500))
    return LLM(provider=provider, model=model, temperature=temperature, max_tokens=max_tokens)
