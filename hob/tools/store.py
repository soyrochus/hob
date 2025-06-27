"""Simple in-memory key-value store primitive."""

from __future__ import annotations

from typing import Any, Dict

from ..core.interfaces import Tool


_STORE: Dict[str, Any] = {}


class Store(Tool):
    """Store or retrieve values."""

    name = "Store"

    def run(self, args: Dict[str, Any], context: Any) -> Any:
        action = args["action"]
        key = args["key"]
        if action == "write":
            _STORE[key] = args.get("value")
            return True
        if action == "read":
            return _STORE.get(key)
        raise ValueError(f"Unknown action {action}")
