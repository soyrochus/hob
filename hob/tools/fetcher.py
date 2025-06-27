"""HTTP Fetcher primitive."""

from __future__ import annotations

from typing import Any, Dict

import requests

from ..core.interfaces import Tool


class Fetcher(Tool):
    """Fetch the raw HTML for a URL."""

    name = "Fetcher"

    def run(self, args: Dict[str, Any], context: Any) -> Dict[str, Any]:
        url = args["url"]
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {"content": response.text, "url": url}
