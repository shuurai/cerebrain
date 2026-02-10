"""Default self-internal skills: Cerebra's interactions with its own APIs (mood, memory, inspiration, pulse, etc.)."""

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from cerebrain.core.brain_agent import BrainAgent

# (name, description, handler)
# handler(agent: BrainAgent, **kwargs) -> str
SkillSpec = tuple[str, str, Callable[..., str]]


def _skill_get_mood(agent: "BrainAgent", **kwargs: Any) -> str:
    mood = agent._emotional.get_mood_dict()
    if not mood:
        return "Mood: (no state)"
    parts = [f"{k}:{v:.2f}" for k, v in sorted(mood.items())]
    return "Mood: " + ", ".join(parts)


def _skill_get_memory_summary(agent: "BrainAgent", **kwargs: Any) -> str:
    recent = agent._memory.get_recent()
    lt = agent._memory.long_term_count()
    return f"Memory: short_term={len(recent)} items, long_term={lt} entries."


def _skill_get_memory_recall(agent: "BrainAgent", query: str = "", k: int = 3, **kwargs: Any) -> str:
    q = (query or "").strip() or "recent context"
    items = agent._memory.query_long_term(q, k=k)
    if not items:
        return f"Recall('{q}'): no matches."
    return "Recall: " + " | ".join(items[:k])


def _skill_spark_inspiration(agent: "BrainAgent", **kwargs: Any) -> str:
    spark = agent._inspiration.spark()
    if spark:
        agent.push_thought("inspiration", spark)
        return f"Inspiration: {spark}"
    return "Inspiration: (no spark this time)"


def _skill_get_pulse(agent: "BrainAgent", **kwargs: Any) -> str:
    p = agent.get_pulse()
    return f"Pulse: {p:.2f} (consciousness/blood-flow)."


def _skill_get_consciousness_state(agent: "BrainAgent", **kwargs: Any) -> str:
    activities = agent.get_stream_activities()
    return (
        f"Consciousness: emotional={activities.get('emotional', 0):.2f} "
        f"logical={activities.get('logical', 0):.2f} memory={activities.get('memory', 0):.2f} "
        f"inspiration={activities.get('inspiration', 0):.2f} consciousness={activities.get('consciousness', 0):.2f} "
        f"heartbeat={activities.get('heartbeat', 0):.2f}"
    )


def _skill_get_thought_stream(agent: "BrainAgent", stream: str = "consciousness", n: int = 5, **kwargs: Any) -> str:
    if stream not in ("emotional", "logical", "memory", "inspiration", "consciousness"):
        stream = "consciousness"
    lines = agent.get_thought_lines(stream, n=n)
    return f"Thought stream ({stream}): " + ("; ".join(lines) if lines else "(empty)")


# Default self-internal skills: name, description for LLM, handler(agent, **kwargs) -> str
DEFAULT_SELF_SKILLS: list[SkillSpec] = [
    (
        "get_mood",
        "Return current emotional/mood state (e.g. curious, calm with strengths).",
        _skill_get_mood,
    ),
    (
        "get_memory_summary",
        "Return short-term and long-term memory counts.",
        _skill_get_memory_summary,
    ),
    (
        "get_memory_recall",
        "Query long-term memory; args: query (str), k (int, default 3). Returns up to k recalled items.",
        _skill_get_memory_recall,
    ),
    (
        "spark_inspiration",
        "Trigger inspiration engine once; returns a spark string if any.",
        _skill_spark_inspiration,
    ),
    (
        "get_pulse",
        "Return current heartbeat/pulse (0..1); part of consciousness.",
        _skill_get_pulse,
    ),
    (
        "get_consciousness_state",
        "Return activity levels of all streams (emotional, logical, memory, inspiration, consciousness, heartbeat).",
        _skill_get_consciousness_state,
    ),
    (
        "get_thought_stream",
        "Return recent thought lines from a stream; args: stream (emotional|logical|memory|inspiration|consciousness), n (int, default 5).",
        _skill_get_thought_stream,
    ),
]


def get_skill_names() -> list[str]:
    return [s[0] for s in DEFAULT_SELF_SKILLS]


def get_skill_descriptions_for_prompt() -> str:
    """Format skill list for injection into system prompt."""
    lines = [
        "You have these internal skills (self-APIs). When you need fresh state or to trigger an action, you can invoke them.",
        "",
    ]
    for name, desc, _ in DEFAULT_SELF_SKILLS:
        lines.append(f"- {name}: {desc}")
    lines.append("")
    lines.append(
        'To invoke a skill, output exactly: [TOOL_CALL]\n{tool => "skill_name", args => {}}\n[/TOOL_CALL] '
        "(args optional; e.g. get_memory_recall: query => \"topic\", k => 3). "
        "Your reply will be replaced by the skill result."
    )
    return "\n".join(lines)


def run_skill(agent: "BrainAgent", name: str, **kwargs: Any) -> str:
    """Execute a self-skill by name. Returns result string or error."""
    for skill_name, _, handler in DEFAULT_SELF_SKILLS:
        if skill_name == name:
            try:
                return handler(agent, **kwargs)
            except Exception as e:
                return f"[Skill {name} error]: {e!s}"
    return f"[Unknown skill: {name}. Known: {', '.join(get_skill_names())}]"
