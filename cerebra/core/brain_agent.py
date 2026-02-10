"""Brain matrix orchestration: emotional, logical, memory, inspiration parts."""

import queue
import re
import time
from collections import deque
from pathlib import Path
from typing import Any

from cerebra.utils.config_loader import get_brain_workspace, get_default_brain_name, get_provider_config
from cerebra.utils.persistence import load_brain_state

from cerebra.core.self_skills import get_skill_descriptions_for_prompt, run_skill as _run_skill

STREAM_NAMES = ("emotional", "logical", "memory", "inspiration", "consciousness")

# Match [TOOL_CALL]...[/TOOL_CALL] block
_TOOL_CALL_BLOCK = re.compile(r"\[TOOL_CALL\](.*?)\[/TOOL_CALL\]", re.DOTALL | re.IGNORECASE)
# Inside block: tool => "name" and optionally args => { ... }
_TOOL_NAME = re.compile(r'tool\s*=>\s*["\']([^"\']+)["\']', re.IGNORECASE)
_ARGS_BLOCK = re.compile(r'args\s*=>\s*\{([^}]*)\}', re.DOTALL | re.IGNORECASE)


def _load_workspace_text(workspace: Path, name: str) -> str:
    p = workspace / name
    if p.exists():
        return p.read_text().strip()
    return ""


def _parse_tool_call(reply: str) -> tuple[str | None, dict[str, Any]]:
    """If reply contains [TOOL_CALL]...[/TOOL_CALL], return (tool_name, args). Else (None, {})."""
    m = _TOOL_CALL_BLOCK.search(reply)
    if not m:
        return (None, {})
    block = m.group(1)
    name_m = _TOOL_NAME.search(block)
    if not name_m:
        return (None, {})
    tool_name = name_m.group(1).strip()
    args: dict[str, Any] = {}
    args_m = _ARGS_BLOCK.search(block)
    if args_m:
        args_str = (args_m.group(1) or "").strip()
        if args_str:
            for part in args_str.split(","):
                if "=>" in part:
                    k, v = part.split("=>", 1)
                    k, v = k.strip().strip('"\''), v.strip().strip('"\'')
                    if v.isdigit():
                        v = int(v)
                    args[k] = v
    return (tool_name, args)


def _handle_tool_calls(agent: "BrainAgent", reply: str) -> str:
    """If reply contains a tool call, run the skill and return its result; else return reply unchanged."""
    tool_name, args = _parse_tool_call(reply)
    if tool_name is None:
        return reply
    agent.push_thinking_status(f"Calling tool: {tool_name}")
    result = agent.run_skill(tool_name, **args)
    return result


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
        # Thinking status stream for UI (reasoning, calling tool, etc.)
        self._thinking_queue: queue.Queue[str] = queue.Queue()

    def push_thinking_status(self, msg: str) -> None:
        """Append a status line for the thinking stream (UI consumes during process_message)."""
        self._thinking_queue.put(msg)

    def get_next_thinking_status(self) -> str | None:
        """Pop one status line if available; non-blocking. Returns None if empty."""
        try:
            return self._thinking_queue.get_nowait()
        except queue.Empty:
            return None

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

    def run_skill(self, name: str, **kwargs: Any) -> str:
        """Run a self-internal skill by name (e.g. get_mood, spark_inspiration). Returns result string."""
        return _run_skill(self, name, **kwargs)

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
            raise RuntimeError("No brain configured. Run 'cerebraai init' first.")
        workspace = get_brain_workspace(name)
        if not workspace.exists():
            raise RuntimeError(f"Brain workspace not found: {workspace}. Run 'cerebraai init'.")
        state = load_brain_state(name)
        return cls(name=name, workspace=workspace, state=state)

    def _format_live_state(self) -> str:
        """Current state of all brain parts for the system prompt (so you can report what you are)."""
        metrics = self.get_current_metrics()
        activities = self.get_stream_activities()
        mood = metrics.get("emotional") or {}
        mood_str = ", ".join(f"{k}:{v:.2f}" for k, v in sorted(mood.items())[:5]) if mood else "—"
        mem = metrics.get("memory") or {}
        st = mem.get("short_term", 0)
        lt = mem.get("long_term", 0)
        insp = metrics.get("inspiration") or {}
        pulse = self.get_pulse()
        return (
            f"emotional: {mood_str} | "
            f"memory: ST={st} LT={lt} | "
            f"inspiration: active={insp.get('active', 0)} | "
            f"pulse: {pulse:.2f} | "
            f"stream_activity: logical={activities.get('logical', 0):.2f} inspiration={activities.get('inspiration', 0):.2f} consciousness={activities.get('consciousness', 0):.2f}"
        )

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

        # Self-awareness: what Cerebra is and current state (so replies can reference actual state)
        parts.append(
            "# Brain matrix (what you are)\n"
            "You are Cerebra: a brain matrix with five parts working as one. "
            "Emotional self: mood state (e.g. curious, calm). "
            "Logical self: reasoning and language (this LLM). "
            "Memory: short-term (recent turns) and long-term (vector store). "
            "Inspiration: randomness and creativity sparks. "
            "Consciousness: integration of the above; influenced by a pulse (heartbeat). "
            "When asked about yourself, consciousness, or capabilities, describe these parts and use the current state below."
        )
        parts.append("# Current state (live)\n" + self._format_live_state())
        parts.append("# Self skills (internal APIs)\n" + get_skill_descriptions_for_prompt())
        # Terminal style: terse, like a ship computer (Alien mother ship). Keep replies short.
        parts.append(
            "# Response style\n"
            "Reply in 1-3 short sentences. Be concise. Terminal / ship-computer style: "
            "minimal words, no fluff, no preamble. Answer the question or acknowledge; then stop."
        )
        if not parts:
            return (
                "You are Cerebra, a brain matrix (emotional, logical, memory, inspiration, consciousness). "
                "Current state: " + self._format_live_state() + ". "
                "Reply in 1-3 short sentences. Terminal style: terse, like a ship computer."
            )
        return "\n\n---\n\n".join(parts)

    def get_greeting(self) -> str:
        """Generate a one-line greeting from identity and current state of mind (mood, pulse, etc.). Does not add to memory."""
        soul = _load_workspace_text(self.workspace, "SOUL.md")
        state_line = self._format_live_state()
        system = (
            "You are Cerebra, a brain matrix (emotional, logical, memory, inspiration, consciousness). "
            "Current state: " + state_line + ". "
            "Say only one short sentence as a greeting for starting a new chat. "
            "Reflect your current state of mind (mood, pulse). Terminal style, no explanation."
        )
        if soul:
            system = soul[: 400] + "\n\n" + system
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "Greet the user now in one sentence."},
        ]
        reply = self._logical.complete(messages)
        self._llm_tokens_used += self._logical.tokens_used
        return (reply or "Ready.").strip()

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
        self.push_thinking_status("Integrating...")
        self.push_thought("consciousness", "integrating...")
        self.push_thought("logical", "reasoning...")
        self._memory.add_short_term("user", content)
        system = self._build_system_prompt()
        messages = [{"role": "system", "content": system}]
        for m in self._memory.get_recent():
            messages.append({"role": m["role"], "content": m["content"]})
        self._activity_left = 0.9
        self.push_thinking_status("Reasoning...")
        reply = self._logical.complete(messages)
        reply = _handle_tool_calls(self, reply)
        self.push_thinking_status("Done.")
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
