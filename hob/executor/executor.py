"""Plan executor walking the AST and invoking tools."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..core.exceptions import ExecutionError
from ..core.interfaces import Executor, Tool
from ..core.registry import ToolRegistry
from ..agent_context import AgentContext


logger = logging.getLogger(__name__)


def resolve_pointer(pointer: Dict[str, Any], trace: List[Any]) -> Any:
    """Resolve a pointer value from the execution trace."""
    idx = pointer["from"]
    value = trace[idx]
    field = pointer.get("field", "")
    if not field:
        return value
    parts = field.replace("[", ".").replace("]", "").split(".")
    for part in parts:
        if not part:
            continue
        try:
            if part.isdigit():
                value = value[int(part)]
            else:
                value = value[part]
        except Exception as exc:  # noqa: BLE001
            raise ExecutionError(f"Failed to resolve pointer: {pointer}") from exc
    return value


class ASTExecutor(Executor):
    """Executor that sequentially runs plan steps."""

    def execute(self, plan: List[Dict[str, Any]], context: AgentContext) -> List[Any]:
        """Execute each step using registered tools."""
        registry = ToolRegistry.get_instance()
        trace: List[Any] = []
        for step in plan:
            tool_cls: type[Tool] = registry.get_tool(step["with"])
            tool = tool_cls()
            args = step.get("args", {})
            # Convert pointers to actual values
            for key, val in list(args.items()):
                if isinstance(val, dict) and set(val.keys()) == {"from", "field"}:
                    args[key] = resolve_pointer(val, trace)
            logger.debug("Running %s with %s", step["with"], args)
            result = tool.run(args, context)
            trace.append(result)
            context.add_trace(result)
        return trace
