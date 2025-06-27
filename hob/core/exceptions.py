"""Custom exceptions used throughout the framework."""


class PlanValidationError(Exception):
    """Raised when a generated plan does not pass validation."""


class ExecutionError(Exception):
    """Raised when execution of a plan fails."""
