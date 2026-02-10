"""Internal model config templates per provider.

Default: max_tokens=8192, temperature=0.7.
Used at brain init and by the LLM client.
"""

from typing import Any

# Global defaults for all providers
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 0.7

# Per-provider: model id and optional overrides
PROVIDER_TEMPLATES: dict[str, dict[str, Any]] = {
    "openrouter": {
        "model": "minimax/minimax-m2",
        "api_base": "https://openrouter.ai/api/v1",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    },
    "openai": {
        "model": "gpt-3.5-turbo",
        "api_base": "https://api.openai.com/v1",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    },
    "anthropic": {
        "model": "claude-3-5-sonnet-20241022",
        "api_base": "https://api.anthropic.com",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    },
    "ollama": {
        "model": "llama3",
        "api_base": "http://localhost:11434",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    },
    "local": {
        "model": "local",
        "api_base": "http://localhost:5000",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    },
}


def get_llm_template(provider: str) -> dict[str, Any]:
    """Return template for a provider (model, api_base, max_tokens, temperature)."""
    key = (provider or "openrouter").strip().lower()
    base = {
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": DEFAULT_TEMPERATURE,
    }
    if key in PROVIDER_TEMPLATES:
        base = {**base, **PROVIDER_TEMPLATES[key]}
    base["provider"] = key
    return base


def get_llm_state_for_brain(provider: str) -> dict[str, Any]:
    """Return llm state dict to store in brain state (provider, model, api_base, max_tokens, temperature)."""
    t = get_llm_template(provider)
    return {
        "provider": t["provider"],
        "model": t["model"],
        "api_base": t.get("api_base", ""),
        "max_tokens": t.get("max_tokens", DEFAULT_MAX_TOKENS),
        "temperature": t.get("temperature", DEFAULT_TEMPERATURE),
    }
