"""Brain matrix orchestration: emotional, logical, memory, inspiration parts."""

import time
from collections import deque
from pathlib import Path
from typing import Any

from cerebra.utils.config_loader import get_brain_workspace, get_default_brain_name, get_provider_config
from cerebra.utils.persistence import load_brain_state

STREAM_NAMES = ("emotional", "logical", "memory", "inspiration", "consciousness")


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
        self._thought_streams = {s: deque(maxlen=24) for s in STREAM_NAMES}
        self._activity_left = 0.4
        self._activity_right = 0.5
        # Heartbeat / blood-flow pulse (consciousness influenced by blood)
        self._pulse = 0.5
        self._last_beat = time.monotonic()

    def get_pulse(self) -> float:
        """Current pulse 0..1 (blood rush into brain); part of consciousness."""
        return max(0.0, min(1.0, self._pulse))

    def push_thought(self, stream: str, text: str) -> None:
        """Append a thought line to a stream (emotional, logical, memory, inspiration, consciousness)."""
        if stream in self._thought_streams:
            self._thought_streams[stream].append(text[:80])

    def get_thought_lines(self, stream: str, n: int = 12) -> list[str]:
        """Return last n lines for a stream (newest at end)."""
        if stream not in self._thought_streams:
            return []
        d = self._thought_streams[stream]
        return list(d)[-n:] if d else []

    def get_activity(self) -> tuple[float, float]:
        """Return (left_brain_activity, right_brain_activity) in 0..1 for display."""
        return (self._activity_left, self._activity_right)

    def get_stream_activities(self) -> dict[str, float]:
        """Return 0..1 activity per stream for left-panel bars."""
        mood = self._emotional.get_mood_dict()
        emotional = max(mood.values()) if mood else 0.5
        mem_fill = min(1.0, len(self._memory.get_recent()) / 7.0) if self._memory else 0.0
        return {
            "emotional": emotional,
            "logical": self._activity_left,
            "memory": mem_fill,
            "inspiration": self._activity_right,
            "consciousness": (self._activity_left + self._activity_right) / 2.0,
            "heartbeat": self.get_pulse(),
        }

    def tick_idle_thoughts(self) -> None:
        """Add one idle thought to a random stream; update heartbeat (blood pulse)."""
        now = time.monotonic()
        r = self._inspiration.get_random_float()
        # Heartbeat: blood rushes in at random intervals, then decays
        if now - self._last_beat >= 0.7 + r * 0.5:
            self._pulse = 0.65 + self._inspiration.get_random_float() * 0.35
            self._last_beat = now
            self.push_thought("consciousness", f"♥ {self._pulse:.2f}")
        else:
            self._pulse = 0.25 + self._pulse * 0.75  # decay toward baseline
        r = self._inspiration.get_random_float()
        stream_idx = int(r * 5) % 5
        stream = STREAM_NAMES[stream_idx]
        mood = self._emotional.get_mood_dict()
        if stream == "emotional" and mood:
            k = max(mood, key=lambda x: mood[x])
            self.push_thought("emotional", f"{k} ({mood[k]:.2f})")
        elif stream == "logical":
            self.push_thought("logical", "idle")
        elif stream == "memory":
            st, lt = len(self._memory.get_recent()), self._memory.long_term_count()
            self.push_thought("memory", f"ST:{st} LT:{lt}")
        elif stream == "inspiration":
            spark = self._inspiration.spark()
            self.push_thought("inspiration", spark or "—")
        else:
            self.push_thought("consciousness", "~")
        self._activity_left = 0.3 + 0.5 * self._inspiration.get_random_float()
        self._activity_right = 0.3 + 0.5 * self._inspiration.get_random_float()

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
        return "\n\n---\n\n".join(parts) if parts else "You are a brain matrix: emotional, logical, memory, and inspiration parts. Respond as one integrated mind."

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
        self._pulse = min(1.0, self._pulse + 0.2)  # blood rush when thinking
        self.push_thought("consciousness", "integrating...")
        self.push_thought("logical", "reasoning...")
        self._memory.add_short_term("user", content)
        system = self._build_system_prompt()
        messages = [{"role": "system", "content": system}]
        for m in self._memory.get_recent():
            messages.append({"role": m["role"], "content": m["content"]})
        self._activity_left = 0.9
        reply = self._logical.complete(messages)
        self._activity_left = 0.5
        self._memory.add_short_term("assistant", reply)
        mood = self._emotional.get_mood_dict()
        if mood:
            k = max(mood, key=lambda x: mood[x])
            self.push_thought("emotional", f"{k} ({mood[k]:.2f})")
        self.push_thought("memory", f"ST:{len(self._memory.get_recent())}")
        spark = self._inspiration.spark()
        if spark:
            self.push_thought("inspiration", spark)
        self._emotional.update_from_interaction(content, reply)
        self._llm_tokens_used += self._logical.tokens_used
        self.push_thought("consciousness", "done")
        return reply
