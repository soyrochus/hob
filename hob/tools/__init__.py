"""Auto-register tool primitives when imported."""

from .searcher import Searcher
from .fetcher import Fetcher
from .parser import Parser
from .compute import Compute
from .store import Store
from ..core.registry import ToolRegistry


def register_all() -> None:
    """Register all tool classes in the global registry."""
    registry = ToolRegistry.get_instance()
    for tool_cls in [Searcher, Fetcher, Parser, Compute, Store]:
        registry.add_tool(tool_cls)


register_all()
