"""Simple REPL to interact with the planner and executor."""

from __future__ import annotations

from pprint import pprint

from hob.agent_context import AgentContext
from hob.executor.executor import ASTExecutor
from hob.planner.planner import DSLPlanner
import hob.tools  # noqa: F401  # register tools


def main() -> None:
    """Start the interactive loop."""
    planner = DSLPlanner()
    executor = ASTExecutor()
    while True:
        goal = input("goal> ")
        if not goal:
            break
        context = AgentContext(goal=goal)
        plan = planner.plan(goal)
        trace = executor.execute(plan, context)
        pprint(trace)


if __name__ == "__main__":
    main()
