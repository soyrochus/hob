"""Rule-based planner implementation for the bicameral agent."""

from __future__ import annotations

from typing import Any, Dict, List

from jsonschema import validate

from ..core.exceptions import PlanValidationError
from ..core.interfaces import Planner
from . import schemas


class DSLPlanner(Planner):
    """Simple planner that generates a plan for a goal."""

    def plan(self, goal: str) -> List[Dict[str, Any]]:
        """Generate and validate a naive plan from a text goal."""
        # Very naive: search then fetch then parse goal.
        plan = [
            {
                "step": "search",
                "with": "Searcher",
                "args": {"query": goal, "top_k": 3},
            },
            {
                "step": "fetch",
                "with": "Fetcher",
                "args": {"url": "https://example.com"},
            },
            {
                "step": "parse",
                "with": "Parser",
                "args": {
                    "raw": {"from": 1, "field": "content"},
                    "schema": {"title": "css:h1"},
                },
            },
        ]
        try:
            validate(plan, schemas.MASTER_SCHEMA)
        except Exception as exc:  # noqa: BLE001
            raise PlanValidationError(str(exc)) from exc
        return plan
