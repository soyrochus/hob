"""HTML parsing primitive."""

from __future__ import annotations

from typing import Any, Dict

from bs4 import BeautifulSoup
from lxml import etree

from ..core.interfaces import Tool


class Parser(Tool):
    """Extract data from HTML using css/xpath/regex."""

    name = "Parser"

    def run(self, args: Dict[str, Any], context: Any) -> Dict[str, Any]:
        raw_html: str = args["raw"]
        schema: Dict[str, str] = args["schema"]
        soup = BeautifulSoup(raw_html, "lxml")
        tree = etree.HTML(raw_html)
        result: Dict[str, Any] = {}
        for key, selector in schema.items():
            if selector.startswith("css:"):
                element = soup.select_one(selector[4:])
                result[key] = element.get_text(strip=True) if element else None
            elif selector.startswith("xpath:"):
                xpath_result = tree.xpath(selector[6:])
                result[key] = xpath_result[0] if xpath_result else None
            elif selector.startswith("regex:"):
                import re

                match = re.search(selector[6:], raw_html)
                result[key] = match.group(0) if match else None
        return result
