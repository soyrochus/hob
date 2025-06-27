"""In-memory memory implementation."""

from __future__ import annotations

from typing import Any, Dict

from ..core.interfaces import Memory


class InMemory(Memory):
    """A simple dictionary-backed memory."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def load(self, key: str) -> Any:
        return self._store.get(key)

    def save(self, key: str, value: Any) -> None:
        self._store[key] = value
