from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ToolExecutionResult:
    run_id: int | None
    tool_name: str
    status: str
    data: Any = None
    error: str | None = None

    def to_model_content(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "data": self.data,
            "error": self.error,
        }
