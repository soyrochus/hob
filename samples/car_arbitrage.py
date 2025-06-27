"""CLI demo for car arbitrage."""

from __future__ import annotations

import argparse
from pprint import pprint

from hob.agent_context import AgentContext
from hob.core.registry import ToolRegistry
from hob.executor.executor import ASTExecutor
from hob.planner.planner import DSLPlanner
import hob.tools  # noqa: F401  # register tools


def main() -> None:
    """Run the car arbitrage sample."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", default="find car deals")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    context = AgentContext(goal=args.goal)
    planner = DSLPlanner()
    executor = ASTExecutor()

    plan = planner.plan(context.goal)
    trace = executor.execute(plan, context)
    pprint(trace)


if __name__ == "__main__":
    main()
