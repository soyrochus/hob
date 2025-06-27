"""Compute primitive performing simple data operations."""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.interfaces import Tool


class Compute(Tool):
    """Perform data processing operations."""

    name = "Compute"

    def run(self, args: Dict[str, Any], context: Any) -> Any:
        op = args["op"]
        inputs = args.get("inputs", [])
        params = args.get("params", {})
        if op == "normalize_prices":
            return [float(str(x).replace("$", "")) for x in inputs]
        if op == "margin_calculation":
            buy = inputs[0]
            sell = inputs[1]
            return [s - b for b, s in zip(buy, sell)]
        if op == "filter":
            predicate = params.get("predicate")
            return [item for item in inputs if eval(predicate, {}, {"item": item})]
        if op == "sort":
            key = params.get("key")
            return sorted(inputs, key=lambda x: x[key])
        if op == "merge":
            return {**inputs[0], **inputs[1]}
        raise ValueError(f"Unknown op {op}")
