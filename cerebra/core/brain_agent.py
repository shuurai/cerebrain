"""Main brain agent orchestration."""

from pathlib import Path
from typing import Any

from cerebra.utils.config_loader import get_brain_workspace, get_default_brain_name, get_provider_config
from cerebra.utils.persistence import load_brain_state


def _load_workspace_text(workspace: Path, name: str) -> str:
    p = workspace / name
    if p.exists():
        return p.read_text().strip()
    return ""


class BrainAgent:
    """Orchestrates emotional, logical, memory, and inspiration components."""

    def __init__(
        self,
        name: str,
        workspace: Path,
        state: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.workspace = Path(workspace)
        self._state = state or {}
        llm_cfg = self._state.get("llm", {})
        self._llm_model = llm_cfg.get("model", "unknown")
        self._llm_tokens_used = 0

        # Subsystems
        from cerebra.core.emotional_self import EmotionalSelf
        from cerebra.core.inspiration_engine import InspirationEngine
        from cerebra.core.logical_self import LogicalSelf
        from cerebra.core.memory_system import MemorySystem
        from cerebra.utils.config_loader import get_memory_vectors_dir

        self._emotional = EmotionalSelf(self._state.get("emotional_profile"))
        self._inspiration = InspirationEngine(self._state.get("inspiration", {}).get("sources"))
        mem_cfg = self._state.get("memory", {})
        cap = mem_cfg.get("short_term_capacity", 7)
        persist_dir = get_memory_vectors_dir(name)
        self._memory = MemorySystem(self.workspace, short_term_capacity=cap, persist_dir=persist_dir)

        provider = llm_cfg.get("provider", "openrouter")
        api_base = llm_cfg.get("api_base") or ""
        prov = get_provider_config(provider)
        if not api_base:
            api_base = prov.get("api_base", "")
        self._logical = LogicalSelf(
            provider=provider,
            model=llm_cfg.get("model", "minimax/minimax-m2"),
            api_key=prov.get("api_key", ""),
            api_base=api_base,
            max_tokens=llm_cfg.get("max_tokens", 8192),
            temperature=llm_cfg.get("temperature", 0.7),
        )

    @classmethod
    def load(cls, brain_name: str | None = None) -> "BrainAgent":
        """Load agent for the given brain name, or default brain."""
        from cerebra.utils.config_loader import ensure_dirs, list_brains_from_disk

        ensure_dirs()
        name = brain_name or get_default_brain_name()
        if not name:
            raise RuntimeError("No brain configured. Run 'cerebra init' first.")
        workspace = get_brain_workspace(name)
        if not workspace.exists():
            raise RuntimeError(f"Brain workspace not found: {workspace}. Run 'cerebra init'.")
        state = load_brain_state(name)
        return cls(name=name, workspace=workspace, state=state)

    def _build_system_prompt(self) -> str:
        soul = _load_workspace_text(self.workspace, "SOUL.md")
        user = _load_workspace_text(self.workspace, "USER.md")
        tools = _load_workspace_text(self.workspace, "TOOLS.md")
        parts = [f"# Identity (SOUL)\n{soul}"] if soul else []
        if user:
            parts.append(f"# User context\n{user}")
        if tools:
            parts.append(f"# Tools\n{tools}")
        lt = self._memory.query_long_term("recent context", k=3)
        if lt:
            parts.append("# Relevant memory\n" + "\n".join(lt))
        return "\n\n---\n\n".join(parts) if parts else "You are a helpful brain agent."

    def get_current_metrics(self) -> dict[str, Any]:
        """Return current metrics for dashboard."""
        mood = self._emotional.get_mood_dict()
        return {
            "emotional": mood,
            "skills": {"logic": 1.0, "creativity": 1.0, "empathy": 1.0},
            "memory": {
                "short_term": len(self._memory.get_recent()),
                "long_term": self._memory.long_term_count(),
            },
            "inspiration": {"active": 1 if self._inspiration._last_spark else 0, "power": 1.0},
            "llm": {"model": self._llm_model, "tokens_used": self._llm_tokens_used},
            "processing": {"speed": 0.0},
        }

    def process_message(self, content: str) -> str:
        """Process one user message and return assistant reply."""
        self._memory.add_short_term("user", content)
        system = self._build_system_prompt()
        messages = [{"role": "system", "content": system}]
        for m in self._memory.get_recent():
            messages.append({"role": m["role"], "content": m["content"]})
        reply = self._logical.complete(messages)
        self._memory.add_short_term("assistant", reply)
        self._emotional.update_from_interaction(content, reply)
        self._inspiration.spark()
        self._llm_tokens_used += self._logical.tokens_used
        return reply
