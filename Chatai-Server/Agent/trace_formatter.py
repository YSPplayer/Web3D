import json
from typing import Any, Mapping


class AgentTraceFormatter:
    """Builds the small, sanitized tool trace exposed to the frontend."""

    _SENSITIVE_KEYS = {
        "api_key",
        "apikey",
        "authorization",
        "credential",
        "credentials",
        "password",
        "passwd",
        "secret",
        "token",
    }
    _STATUS_LABELS = {
        "running": "执行中",
        "success": "完成",
        "failed": "失败",
        "timeout": "超时",
        "denied": "已拒绝",
    }

    def from_event(self, event: Mapping[str, Any]) -> dict:
        event_type = event.get("type")
        status = "running" if event_type == "tool_start" else str(
            event.get("status") or "failed"
        )
        trace_id = str(event.get("trace_id") or self._trace_id(event))
        arguments = event.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}

        return {
            "type": "agent_trace",
            "action": "start" if event_type == "tool_start" else "finish",
            "trace": {
                "id": trace_id,
                "kind": "tool",
                "toolName": str(event.get("tool_name") or "unknown_tool"),
                "command": self.format_command(
                    str(event.get("tool_name") or "unknown_tool"),
                    arguments,
                ),
                "status": status,
                "summary": self.format_summary(
                    status,
                    event.get("data"),
                ),
            },
        }

    def from_audit_row(self, row: Mapping[str, Any]) -> dict:
        arguments = self._load_json(row.get("arguments_json"), {})
        result = self._load_json(row.get("result_json"), None)
        run_id = row.get("id")
        step_index = row.get("step_index") or 0
        return {
            "id": f"tool-{step_index}-{run_id}",
            "kind": "tool",
            "toolName": str(row.get("tools_name") or "unknown_tool"),
            "command": self.format_command(
                str(row.get("tools_name") or "unknown_tool"),
                arguments if isinstance(arguments, dict) else {},
            ),
            "status": str(row.get("status") or "failed"),
            "summary": self.format_summary(
                str(row.get("status") or "failed"),
                result,
            ),
        }

    def format_command(self, tool_name: str, arguments: Mapping[str, Any]) -> str:
        safe_arguments = self._sanitize(arguments)
        parts = [
            f"{key}={json.dumps(value, ensure_ascii=False, default=str)}"
            for key, value in safe_arguments.items()
        ]
        command = f"{tool_name}({', '.join(parts)})"
        return self._limit_text(command, 1000)

    def format_summary(self, status: str, data: Any) -> str:
        label = self._STATUS_LABELS.get(status, status)
        if status != "success" or not isinstance(data, dict):
            return label

        directory_count = data.get("directory_count")
        file_count = data.get("file_count")
        if isinstance(directory_count, int) and isinstance(file_count, int):
            return f"{label} · {directory_count} 个目录，{file_count} 个文件"
        if isinstance(directory_count, int):
            return f"{label} · {directory_count} 个目录"
        if isinstance(file_count, int):
            return f"{label} · {file_count} 个文件"
        return label

    def _trace_id(self, event: Mapping[str, Any]) -> str:
        step_index = event.get("step_index") or 0
        run_id = event.get("run_id")
        return f"tool-{step_index}-{run_id if run_id is not None else 'pending'}"

    def _sanitize(self, value: Any, key: str = "") -> Any:
        if self._is_sensitive_key(key):
            return "***"
        if isinstance(value, Mapping):
            return {
                str(item_key): self._sanitize(item_value, str(item_key))
                for item_key, item_value in value.items()
            }
        if isinstance(value, list):
            return [self._sanitize(item) for item in value[:50]]
        if isinstance(value, str):
            return self._limit_text(value, 500)
        return value

    def _is_sensitive_key(self, key: str) -> bool:
        normalized = key.lower().replace("-", "_")
        return normalized in self._SENSITIVE_KEYS or any(
            normalized.endswith(f"_{name}")
            for name in self._SENSITIVE_KEYS
        )

    @staticmethod
    def _limit_text(value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return value[:limit] + "…"

    @staticmethod
    def _load_json(value: Any, default: Any) -> Any:
        if value is None:
            return default
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default


agent_trace_formatter = AgentTraceFormatter()
