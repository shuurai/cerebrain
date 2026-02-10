"""Real-time metrics display."""

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from cerebra.core.brain_agent import BrainAgent


def _format_mood(mood_data: dict) -> str:
    if not mood_data:
        return "—"
    parts = []
    for k, v in sorted(mood_data.items(), key=lambda x: -x[1])[:4]:
        if v > 0.2:
            bar = "█" * int(v * 5) + "░" * (5 - int(v * 5))
            parts.append(f"{k}:{bar}")
    return " | ".join(parts) if parts else "—"


def _format_skills(skills_data: dict) -> str:
    if not skills_data:
        return "baseline"
    active = [f"{k}↑{v:.1f}" for k, v in skills_data.items() if v > 1.0]
    return " ".join(active) if active else "baseline"


def generate_metrics_panel(brain: "BrainAgent") -> Panel:
    """Build a Rich panel with current brain metrics."""
    metrics = brain.get_current_metrics()
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Mood", _format_mood(metrics.get("emotional", {})))
    table.add_row("Skills", _format_skills(metrics.get("skills", {})))
    mem = metrics.get("memory", {})
    table.add_row("Memory", f"ST: {mem.get('short_term', 0)}/7 | LT: {mem.get('long_term', 0)}")
    insp = metrics.get("inspiration", {})
    table.add_row("Inspiration", f"Active: {insp.get('active', 0)} | Power: {insp.get('power', 0):.1f}")
    llm = metrics.get("llm", {})
    table.add_row("LLM", f"{llm.get('model', '—')} | Tokens: {llm.get('tokens_used', 0)}")
    table.add_row("Thinking", f"{metrics.get('processing', {}).get('speed', 0):.0f}ms")
    return Panel(table, title="[bold]Brain Metrics[/bold]", border_style="blue", padding=(1, 2))
