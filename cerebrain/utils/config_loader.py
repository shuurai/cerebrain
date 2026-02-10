"""Configuration loading and paths."""

import os
from pathlib import Path
from typing import Any

import yaml

# Full config template: every variable visible for manual edit. Defaults only.
FULL_CONFIG_TEMPLATE: dict[str, Any] = {
    "default_brain": "default",
    "server": {
        "port": 17971,
    },
    "llm_defaults": {
        "max_tokens": 8192,
        "temperature": 0.7,
    },
    "providers": {
        "openrouter": {
            "api_key": "",
            "api_base": "https://openrouter.ai/api/v1",
        },
        "openai": {
            "api_key": "",
            "api_base": "https://api.openai.com/v1",
        },
        "anthropic": {
            "api_key": "",
            "api_base": "https://api.anthropic.com",
        },
        "ollama": {
            "api_key": "",
            "api_base": "http://localhost:11434",
        },
        "local": {
            "api_key": "",
            "api_base": "http://localhost:5000",
        },
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base. Override values take precedence."""
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def get_full_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return full config with all keys: template + loaded file + overrides."""
    loaded = load_config()
    base = _deep_merge(FULL_CONFIG_TEMPLATE, loaded)
    if overrides:
        base = _deep_merge(base, overrides)
    return base


def get_config_dir() -> Path:
    """Config directory: ~/.cerebrain."""
    return Path(os.path.expanduser("~")).resolve() / ".cerebrain"


def get_config_path() -> Path:
    """Main config file path."""
    return get_config_dir() / "config.yaml"


def get_data_dir() -> Path:
    """Data directory (brains, vectors, logs): ~/.cerebrain."""
    return get_config_dir()


def get_workspace_dir() -> Path:
    """Workspace root for default brain (SOUL, USER, etc.)."""
    return get_data_dir() / "workspace"


def get_brain_workspace(brain_name: str) -> Path:
    """Workspace path for a given brain."""
    return get_data_dir() / "workspace" / _safe_brain_name(brain_name)


def get_brain_states_dir() -> Path:
    """Directory for saved brain state files."""
    return get_data_dir() / "brain_states"


def get_memory_vectors_dir(brain_name: str) -> Path:
    """Vector DB storage for a brain (self-contained)."""
    return get_data_dir() / "memory_vectors" / _safe_brain_name(brain_name)


def _safe_brain_name(name: str) -> str:
    """Sanitize brain name for use in paths."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "default"


def ensure_dirs() -> None:
    """Create config and data directories if missing."""
    get_config_dir().mkdir(parents=True, exist_ok=True)
    (get_data_dir() / "workspace").mkdir(parents=True, exist_ok=True)
    (get_data_dir() / "brain_states").mkdir(parents=True, exist_ok=True)
    (get_data_dir() / "logs").mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML config; return empty dict if missing."""
    path = config_path or get_config_path()
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_config(data: dict[str, Any], config_path: Path | None = None) -> None:
    """Save YAML config. Merges data into full template so all variables are visible."""
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    full = get_full_config(data)
    with open(path, "w") as f:
        f.write("# Cerebrain config — edit any value. All supported keys are listed.\n")
        yaml.safe_dump(full, f, default_flow_style=False, sort_keys=False)


def get_default_port() -> int:
    """Default API server port from config."""
    cfg = load_config()
    port = cfg.get("server", {}).get("port") or cfg.get("port")
    if port is not None:
        try:
            return int(port)
        except (TypeError, ValueError):
            pass
    return 17971


def get_default_brain_name() -> str | None:
    """First brain name from config, or first found in workspace."""
    cfg = load_config()
    if cfg.get("default_brain"):
        return cfg["default_brain"]
    brains = list_brains_from_disk()
    return brains[0] if brains else None


def list_brains_from_disk() -> list[str]:
    """List brain names from workspace subdirs."""
    workspace = get_data_dir() / "workspace"
    if not workspace.exists():
        return []
    return [d.name for d in workspace.iterdir() if d.is_dir() and not d.name.startswith(".")]


# OpenRouter and other providers: standard API base URLs (OpenAI-compatible)
PROVIDER_API_BASES: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "ollama": "http://localhost:11434",
    "local": "http://localhost:5000",
}


def get_provider_config(provider: str) -> dict[str, Any]:
    """Get api_key and api_base for a provider from config. Used by LLM client."""
    cfg = load_config()
    providers = cfg.get("providers") or {}
    # Support both snake_case and camelCase
    key = provider.lower()
    p = providers.get(key) or providers.get(key.replace("_", ""))
    if not p:
        return {"api_key": "", "api_base": PROVIDER_API_BASES.get(provider, "")}
    api_key = p.get("api_key") or p.get("apiKey") or ""
    api_base = p.get("api_base") or p.get("apiBase") or PROVIDER_API_BASES.get(provider, "")
    return {"api_key": api_key, "api_base": api_base}
