class AgentToolError(Exception):
    """Agent 工具模块的基础异常。"""


class ToolNotFoundError(AgentToolError):
    pass


class ToolPermissionError(AgentToolError):
    pass


class ToolArgumentError(AgentToolError):
    pass


class ToolRepositoryError(AgentToolError):
    pass
