"""Abstract interfaces for planner, executor, tools and memory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List


class Tool(ABC):
    """Abstract base class for a primitive action."""

    name: str

    @abstractmethod
    def run(self, args: Dict[str, Any], context: "AgentContext") -> Any:
        """Execute the tool with given arguments."""


class Memory(ABC):
    """Abstract base class for memory backends."""

    @abstractmethod
    def load(self, key: str) -> Any:
        """Load a value from memory."""

    @abstractmethod
    def save(self, key: str, value: Any) -> None:
        """Save a value to memory."""


class Planner(ABC):
    """Planner interface that transforms a goal into a plan."""

    @abstractmethod
    def plan(self, goal: str) -> List[Dict[str, Any]]:
        """Return a validated plan for a textual goal."""


class Executor(ABC):
    """Executor interface that runs a plan."""

    @abstractmethod
    def execute(self, plan: List[Dict[str, Any]], context: "AgentContext") -> List[Any]:
        """Execute the plan and return the trace."""
