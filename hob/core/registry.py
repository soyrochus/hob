"""Tool registry for looking up primitives by name."""

from __future__ import annotations

from typing import Dict, Type

from .interfaces import Tool


class ToolRegistry:
    """Singleton registry mapping tool names to classes."""

    _instance: "ToolRegistry | None" = None

    def __init__(self) -> None:
        self._tools: Dict[str, Type[Tool]] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Return the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_tool(self, tool_cls: Type[Tool]) -> None:
        """Register a tool class."""
        self._tools[tool_cls.name] = tool_cls

    def get_tool(self, name: str) -> Type[Tool]:
        """Retrieve a tool class by name."""
        return self._tools[name]
