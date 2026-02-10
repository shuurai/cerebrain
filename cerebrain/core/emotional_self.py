"""Mood and emotion dynamics."""

from typing import Any


class EmotionalSelf:
    """Emotional state: baseline traits + light drift from interaction."""

    DEFAULT_TRAITS = {"curious": 0.7, "creative": 0.6, "focused": 0.5, "empathetic": 0.6}

    def __init__(self, baseline: dict[str, Any] | None = None) -> None:
        self.baseline = baseline or {}
        traits = self.baseline.get("traits") or self.DEFAULT_TRAITS
        self.current: dict[str, float] = dict(traits)

    def update_from_interaction(self, content: str, response: str) -> None:
        """Slight mood drift from interaction (e.g. longer reply -> slight creativity bump)."""
        # Minimal heuristic: response length and content hint
        if len(response) > 200:
            self._nudge("creative", 0.02)
        if "?" in content:
            self._nudge("curious", 0.02)
        self._clamp()

    def _nudge(self, trait: str, delta: float) -> None:
        if trait in self.current:
            self.current[trait] = min(1.0, max(0.0, self.current[trait] + delta))

    def _clamp(self) -> None:
        for k in self.current:
            self.current[k] = min(1.0, max(0.0, self.current[k]))

    def get_mood_dict(self) -> dict[str, float]:
        """Current mood as dict for metrics."""
        return dict(self.current)
