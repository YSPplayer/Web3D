"""旧名称的兼容入口。

新代码应直接使用 ToolDispatcher。这个别名只用于避免旧导入立即失效。
"""

from Agent.tool_dispatcher import ToolDispatcher


CommandManager = ToolDispatcher

__all__ = ["CommandManager"]
