"""Default config files and model templates."""

from cerebra.config.model_templates import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    get_llm_state_for_brain,
    get_llm_template,
    PROVIDER_TEMPLATES,
)

__all__ = [
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "PROVIDER_TEMPLATES",
    "get_llm_template",
    "get_llm_state_for_brain",
]
