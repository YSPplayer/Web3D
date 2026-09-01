from collections.abc import Callable
from typing import Any


CompletionRule = Callable[[dict, Any, dict], bool]


class ToolCompletionPolicy:
    """判断成功工具结果是否已经足够进入最终回答阶段。"""

    def __init__(self):
        self._rules: dict[str, CompletionRule] = {
            "list_directory": self._list_directory_ready,
        }

    def can_finalize(
        self,
        tool_name: str,
        arguments: dict,
        result_data: Any,
        *,
        request_context: dict | None = None,
    ) -> bool:
        rule = self._rules.get(tool_name)
        if rule is None:
            return False
        return rule(arguments, result_data, request_context or {})

    @staticmethod
    def _list_directory_ready(
        arguments: dict,
        result_data: Any,
        request_context: dict,
    ) -> bool:
        if not request_context.get("directories_only", False):
            return False
        if arguments.get("max_depth") != 0:
            return False
        if not isinstance(result_data, dict):
            return False
        if result_data.get("truncated") is not False:
            return False

        entries = result_data.get("entries")
        directory_count = result_data.get("directory_count")
        if not isinstance(entries, list) or not isinstance(directory_count, int):
            return False
        if any(
            not isinstance(entry, dict)
            or entry.get("type") != "directory"
            for entry in entries
        ):
            return False
        return directory_count == len(entries)


tool_completion_policy = ToolCompletionPolicy()
