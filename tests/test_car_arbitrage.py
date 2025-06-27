"""Integration test for the car arbitrage sample."""

from hob.agent_context import AgentContext
from hob.executor.executor import ASTExecutor
from hob.planner.planner import DSLPlanner
import hob.tools  # noqa: F401  # register tools


def test_car_arbitrage() -> None:
    planner = DSLPlanner()
    executor = ASTExecutor()
    context = AgentContext(goal="find deals")
    plan = planner.plan(context.goal)
    trace = executor.execute(plan, context)
    assert trace
