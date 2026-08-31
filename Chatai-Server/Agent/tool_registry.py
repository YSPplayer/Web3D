from collections.abc import Iterable

from Agent.base import PythonTool, ToolDefinition
from Agent.exceptions import ToolNotFoundError


class ToolRegistry:
    def __init__(self, tools: Iterable[PythonTool] | None = None):
        self._tools: dict[str, PythonTool] = {}
        for tool in tools or ():
            self.register(tool)

    def register(self, tool: PythonTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"工具重复注册：{tool.name}")
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> PythonTool:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotFoundError(f"Python 工具未注册：{tool_name}")
        return tool

    def definitions(self) -> list[ToolDefinition]:
        return [tool.definition() for tool in self._tools.values()]

    def model_schemas(self, enabled_names: set[str] | None = None) -> list[dict]:
        tools = self._tools.values()
        if enabled_names is not None:
            tools = (tool for tool in tools if tool.name in enabled_names)
        return [tool.model_schema() for tool in tools]

    def names(self) -> set[str]:
        return set(self._tools)
