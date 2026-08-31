from Agent.tool_dispatcher import ToolDispatcher
from Agent.tool_registry import ToolRegistry
from Agent.tools import default_tools


def build_default_registry() -> ToolRegistry:
    return ToolRegistry(default_tools())


def create_default_dispatcher(db_manager) -> ToolDispatcher:
    from Data.agent_tool_repository import AgentToolRepository

    repository = AgentToolRepository(db_manager)
    return ToolDispatcher(build_default_registry(), repository)
