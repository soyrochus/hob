"""Domain specific language helpers for the planner."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Pointer:
    """A reference to a field from a previous step result."""

    from_step: int
    field: str


def pointer(from_step: int, field: str) -> Dict[str, Any]:
    """Helper to create pointer dictionaries."""
    return {"from": from_step, "field": field}
