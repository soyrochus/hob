"""Searcher primitive."""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.interfaces import Tool


class Searcher(Tool):
    """Return mock search results for a query."""

    name = "Searcher"

    def run(self, args: Dict[str, Any], context: Any) -> List[Dict[str, str]]:
        query = args.get("query", "")
        top_k = int(args.get("top_k", 3))
        return [{"url": f"https://example.com/{i}", "query": query} for i in range(top_k)]
