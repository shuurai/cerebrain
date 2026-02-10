"""Brain state persistence: list, load, save, export."""

import json
from pathlib import Path
from typing import Any

import yaml

from cerebra.utils.config_loader import (
    ensure_dirs,
    get_brain_states_dir,
    get_brain_workspace,
    get_data_dir,
    list_brains_from_disk,
    load_config,
)


def list_brains() -> list[str]:
    """List available brain names (from config default + workspace dirs)."""
    cfg = load_config()
    default = cfg.get("default_brain")
    from_disk = list_brains_from_disk()
    if default and default not in from_disk:
        from_disk.insert(0, default)
    seen = set()
    out = []
    for b in from_disk:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


def get_brain_state_path(brain_name: str) -> Path:
    """Path to brain state file (JSON)."""
    ensure_dirs()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in brain_name).strip("_") or "default"
    return get_brain_states_dir() / f"{safe}.json"


def load_brain_state(brain_name: str) -> dict[str, Any] | None:
    """Load brain state dict or None if not found."""
    path = get_brain_state_path(brain_name)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def save_brain_state(brain_name: str, state: dict[str, Any]) -> Path:
    """Save brain state; return path."""
    ensure_dirs()
    path = get_brain_state_path(brain_name)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path


def export_brain(brain_name: str, fmt: str = "json") -> Path | None:
    """Export brain state to a file in data dir; return path or None."""
    state = load_brain_state(brain_name)
    if state is None:
        workspace = get_brain_workspace(brain_name)
        if workspace.exists():
            state = {"brain": brain_name, "workspace": str(workspace), "soul": " see SOUL.md"}
        else:
            return None
    ensure_dirs()
    export_dir = get_data_dir() / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in brain_name).strip("_") or "default"
    if fmt == "json":
        path = export_dir / f"{safe}.json"
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
    elif fmt == "yaml":
        path = export_dir / f"{safe}.yaml"
        with open(path, "w") as f:
            yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)
    else:
        path = export_dir / f"{safe}.txt"
        with open(path, "w") as f:
            f.write(json.dumps(state, indent=2))
    return path
