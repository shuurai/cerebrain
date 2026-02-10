"""Natural randomness sources (ANU Quantum, random.org) with system entropy fallback."""

import hashlib
import time
from dataclasses import dataclass
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore


@dataclass
class RandomnessSource:
    """Single randomness source (URL or name)."""
    name: str
    url: Optional[str] = None
    priority: int = 1
    is_active: bool = True


class SystemEntropy:
    """Fallback pseudo-random with system entropy mixing."""

    def get_float(self) -> float:
        sources = [
            time.time_ns() % 1000,
            hash(str(time.process_time())) % 1000,
            hash(str(id(object()))) % 1000,
        ]
        mixed = hashlib.sha256(str(sources).encode()).hexdigest()
        return int(mixed[:8], 16) / 0xFFFFFFFF


class NaturalRandomness:
    """Random float 0-1 from best available source: ANU Quantum, random.org, then system entropy."""

    def __init__(self) -> None:
        self.sources = self._initialize_sources()
        self.fallback = SystemEntropy()

    def _initialize_sources(self) -> list[RandomnessSource]:
        return [
            RandomnessSource(
                name="anu_quantum",
                url="https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint16",
                priority=1,
            ),
            RandomnessSource(
                name="random_org",
                url="https://www.random.org/integers/?num=1&min=0&max=10000&col=1&base=10&format=plain",
                priority=2,
            ),
        ]

    def get_random_float(self) -> float:
        """Return random float in [0, 1] from best available source."""
        for source in sorted(self.sources, key=lambda x: x.priority):
            if not source.is_active:
                continue
            try:
                value = self._fetch_from_source(source)
                if value is not None:
                    if source.name == "anu_quantum":
                        return value / 65535.0
                    return value / 10000.0
            except Exception:
                source.is_active = False
        return self.fallback.get_float()

    def _fetch_from_source(self, source: RandomnessSource) -> Optional[int]:
        if not source.url or not requests:
            return None
        if source.name == "anu_quantum":
            r = requests.get(source.url, timeout=2)
            r.raise_for_status()
            data = r.json()
            return data.get("data", [0])[0]
        if source.name == "random_org":
            r = requests.get(source.url, timeout=3)
            r.raise_for_status()
            return int(r.text.strip())
        return None
