"""Shared context objects for the bicameral agent."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentContext:
    """Holds user goal, optional memory snapshot and metadata."""

    goal: str
    memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace: List[Any] = field(default_factory=list)

    def add_trace(self, item: Any) -> None:
        """Append an item to the execution trace."""
        self.trace.append(item)
