"""JSON-based persistent memory for individual agents.

Each agent keeps its own conversation history in a small JSON file under
``data/memory/<agent_name>.json``.  The file is gitignored so it stays local
to the device (Raspberry Pi or development machine) and is never committed.

Only the last ``max_exchanges`` user/assistant pairs are retained so the file
stays small and the LLM context window is not overwhelmed.
"""

import json
from pathlib import Path

from nira_backend.config import get_data_dir


class PersistentMemory:
    """
    Lightweight, file-backed conversation memory for a single agent.

    Args:
        agent_name: Unique name for the agent (used as the filename).
        max_exchanges: Maximum number of user/assistant exchanges to keep.
            Older exchanges are dropped when the limit is exceeded.
        data_dir: Override the data directory (useful in tests).
    """

    def __init__(
        self,
        agent_name: str,
        max_exchanges: int = 20,
        data_dir: Path | None = None,
    ) -> None:
        root = data_dir if data_dir is not None else get_data_dir()
        self._path = root / "memory" / f"{agent_name}.json"
        self._max_messages = max_exchanges * 2  # user + assistant per exchange
        self._history: list[dict[str, str]] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_exchange(self, user_message: str, assistant_message: str) -> None:
        """Append a user/assistant exchange and persist to disk."""
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": assistant_message})
        if len(self._history) > self._max_messages:
            self._history = self._history[-self._max_messages :]
        self._save()

    def get_context_messages(self) -> list:
        """
        Return the stored history as LangChain message objects.

        Returns:
            List of ``HumanMessage`` / ``AIMessage`` instances.
        """
        from langchain_core.messages import AIMessage, HumanMessage

        result = []
        for msg in self._history:
            if msg["role"] == "user":
                result.append(HumanMessage(content=msg["content"]))
            else:
                result.append(AIMessage(content=msg["content"]))
        return result

    def clear(self) -> None:
        """Erase all stored history and delete the backing file."""
        self._history = []
        if self._path.exists():
            self._path.unlink()

    @property
    def message_count(self) -> int:
        """Total number of individual messages stored (user + assistant)."""
        return len(self._history)

    @property
    def exchange_count(self) -> int:
        """Number of complete user/assistant exchanges stored."""
        return len(self._history) // 2

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._history = data.get("history", [])
            except (json.JSONDecodeError, OSError):
                self._history = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"history": self._history}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
