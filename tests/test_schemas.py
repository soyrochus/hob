"""Unit tests for plan schema validation."""

from hob.core.exceptions import PlanValidationError
from hob.planner import schemas
from hob.planner.planner import DSLPlanner


def test_invalid_plan_raises() -> None:
    planner = DSLPlanner()
    bad_plan = [{"step": "bad", "with": "Searcher", "args": {"top_k": 0}}]
    try:
        from jsonschema import validate

        validate(bad_plan, schemas.MASTER_SCHEMA)
    except Exception:
        pass
    else:
        raise AssertionError("validation should fail")

    try:
        planner.plan(123)  # type: ignore[arg-type]
    except PlanValidationError:
        pass
    else:
        raise AssertionError("expected PlanValidationError")
