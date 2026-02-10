"""Randomness and creativity triggers using natural randomness."""

from typing import Any

from cerebrain.utils.randomness import NaturalRandomness

# Association chains for "spark" — personality, process, psychology, cross-domain.
# Format: A → B → C (evocative leaps). Extend via config later.
SPARK_TEMPLATES = [
    # Science & discovery
    "Gravity → Apple → Newton",
    "particle → wave → duality",
    "thought → word → action",
    "question → experiment → proof",
    "chaos → pattern → law",
    "error → correction → insight",
    "dark → telescope → cosmos",
    "cell → division → life",
    "flame → oxygen → burn",
    "seed → code → forest",
    # Psychology & mind
    "fear → breath → courage",
    "memory → dream → insight",
    "shadow → light → wholeness",
    "mask → mirror → self",
    "wound → scar → story",
    "doubt → question → clarity",
    "habit → groove → identity",
    "projection → reflection → truth",
    "repression → symptom → signal",
    "desire → lack → creation",
    "anxiety → edge → presence",
    "trauma → freeze → thaw",
    "attachment → loss → freedom",
    "ego → crack → humility",
    # Process & becoming
    "seed → root → bloom",
    "blank → stroke → meaning",
    "silence → note → song",
    "stumble → fall → rise",
    "block → pause → pivot",
    "practice → groove → mastery",
    "mistake → loop → learning",
    "constraint → focus → form",
    "repetition → ritual → meaning",
    "friction → heat → change",
    "void → gesture → art",
    "chaos → order → beauty",
    "fragment → collage → whole",
    "improvisation → accident → discovery",
    # Emotion & mood
    "grief → acceptance → peace",
    "rage → channel → power",
    "joy → overflow → gift",
    "sorrow → depth → compassion",
    "loneliness → longing → connection",
    "wonder → pause → gratitude",
    "boredom → rest → curiosity",
    "envy → mirror → desire",
    "shame → exposure → release",
    "love → risk → trust",
    "anger → boundary → respect",
    "melancholy → twilight → poetry",
    # Nature & body
    "breath → pulse → life",
    "storm → calm → clarity",
    "river → stone → smooth",
    "fire → ash → rebirth",
    "winter → sleep → spring",
    "root → soil → hold",
    "wing → wind → flight",
    "blood → heart → beat",
    "bone → structure → stand",
    "skin → touch → boundary",
    "hunger → hunt → feast",
    "thirst → source → drink",
    # Philosophy & meaning
    "loss → void → presence",
    "death → limit → urgency",
    "time → flow → now",
    "past → ghost → lesson",
    "future → pull → choice",
    "self → other → us",
    "word → ear → understanding",
    "silence → space → listening",
    "paradox → hold → wisdom",
    "suffering → meaning → Viktor",
    "absurd → laugh → freedom",
    "nothing → something → creation",
    "illusion → crack → real",
    # Art & creation
    "blank → mark → meaning",
    "noise → filter → signal",
    "clay → hand → shape",
    "ink → spill → accident",
    "voice → echo → chorus",
    "image → symbol → myth",
    "rhythm → break → surprise",
    "tension → release → resolution",
    "improvisation → mistake → gift",
    "craft → obsession → masterpiece",
    "imitation → theft → originality",
    "constraint → form → sonnet",
    # Connection & relation
    "self → other → us",
    "speaker → listener → bridge",
    "give → receive → balance",
    "boundary → respect → intimacy",
    "vulnerability → risk → trust",
    "mirror → recognition → kinship",
    "stranger → story → neighbor",
    "enemy → shadow → teacher",
    "ally → side → tribe",
    "witness → presence → healing",
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
