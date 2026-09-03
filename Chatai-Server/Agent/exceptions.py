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


class ToolConflictError(AgentToolError):
    pass


class ToolValidationError(AgentToolError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("；".join(errors))


class ToolStorageError(AgentToolError):
    pass


class ToolRuntimeError(AgentToolError):
    pass


class ToolRuntimeTimeoutError(ToolRuntimeError):
    pass


class ToolRuntimeOutputError(ToolRuntimeError):
    pass
