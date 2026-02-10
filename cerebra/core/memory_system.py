"""Short-term buffer and long-term vector store (optional ChromaDB)."""

import time
import uuid
from pathlib import Path
from typing import Any

# Optional ChromaDB for long-term vector memory (self-contained, persist_directory)
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None  # type: ignore


class MemorySystem:
    """Short-term buffer + long-term vector store (ChromaDB if available)."""

    def __init__(
        self,
        workspace: Path,
        short_term_capacity: int = 7,
        persist_dir: Path | None = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.short_term_capacity = short_term_capacity
        self._short_term: list[dict[str, str]] = []
        self._persist_dir = persist_dir
        self._chroma_client = None
        self._chroma_collection = None
        if CHROMADB_AVAILABLE and persist_dir:
            persist_dir.mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                "long_term", metadata={"hnsw:space": "cosine"}
            )

    def add_short_term(self, role: str, content: str) -> None:
        """Append to short-term; evict if over capacity."""
        self._short_term.append({"role": role, "content": content})
        if len(self._short_term) > self.short_term_capacity:
            self._short_term.pop(0)

    def get_recent(self, n: int | None = None) -> list[dict[str, str]]:
        """Last n short-term items (default: all up to capacity)."""
        cap = n if n is not None else self.short_term_capacity
        return self._short_term[-cap:]

    def add_long_term(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a document to long-term vector store (if ChromaDB available)."""
        if not self._chroma_collection:
            return
        uid = f"lt_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        self._chroma_collection.add(
            documents=[text],
            ids=[uid],
            metadatas=[metadata or {}],
        )

    def query_long_term(self, query: str, k: int = 5) -> list[str]:
        """Vector search; returns list of document strings (empty if no ChromaDB)."""
        if not self._chroma_collection:
            return []
        try:
            result = self._chroma_collection.query(query_texts=[query], n_results=k)
            docs = result.get("documents", [[]])
            return list(docs[0]) if docs else []
        except Exception:
            return []

    def long_term_count(self) -> int:
        """Approximate number of items in long-term store."""
        if not self._chroma_collection:
            return 0
        try:
            return self._chroma_collection.count()
        except Exception:
            return 0
