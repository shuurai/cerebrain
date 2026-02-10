"""Randomness and creativity triggers using natural randomness."""

from typing import Any

from cerebra.utils.randomness import NaturalRandomness


# Simple association chains for "spark" (can be extended from config)
SPARK_TEMPLATES = [
    "Gravity → Apple → Newton",
    "particle → wave → duality",
    "thought → word → action",
]


class InspirationEngine:
    """Natural randomness and occasional inspiration sparks."""

    def __init__(self, sources: list[dict[str, Any]] | None = None) -> None:
        self._random = NaturalRandomness()
        self.sources = sources or []
        self._last_spark: str | None = None

    def get_random_float(self) -> float:
        """0–1 from best available source."""
        return self._random.get_random_float()

    def spark(self) -> str | None:
        """With ~30% chance return a short inspiration string."""
        if self._random.get_random_float() > 0.7:
            return None
        idx = int(self._random.get_random_float() * len(SPARK_TEMPLATES)) % len(SPARK_TEMPLATES)
        self._last_spark = SPARK_TEMPLATES[idx]
        return self._last_spark
