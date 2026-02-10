"""LLM interface: OpenAI-compatible API (OpenRouter, OpenAI, Ollama, local)."""

from typing import Any

import httpx


class LogicalSelf:
    """Calls LLM via OpenAI-compatible chat/completions API."""

    def __init__(
        self,
        provider: str = "openrouter",
        model: str = "",
        api_key: str = "",
        api_base: str = "",
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ) -> None:
        self.provider = provider
        self.model = model or "minimax/minimax-m2"
        self.api_key = api_key
        self.api_base = (api_base or "").rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._tokens_used = 0

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Call chat/completions and return assistant message content."""
        url = f"{self.api_base}/chat/completions" if self.api_base else ""
        if not url:
            return "[Cerebra] No API base configured. Set LLM api_base in brain state or providers in config."
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": kwargs.get("model") or self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPStatusError as e:
            return f"[Cerebra] LLM error {e.response.status_code}: {e.response.text[:200]}"
        except Exception as e:
            return f"[Cerebra] LLM request failed: {e!s}"

        choice = (data.get("choices") or [None])[0]
        if not choice:
            return "[Cerebra] No response from LLM."
        msg = choice.get("message") or {}
        content = (msg.get("content") or "").strip()
        usage = data.get("usage") or {}
        self._tokens_used += usage.get("total_tokens", 0)
        return content or "[Cerebra] Empty LLM response."
