import asyncio
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from uuid import uuid4

from Agent.base import PythonTool
from Agent.context import ToolContext


class LimitedTextBuffer(io.TextIOBase):
    def __init__(self, max_bytes: int):
        self.max_bytes = max(0, max_bytes)
        self._data = bytearray()
        self.truncated = False

    def writable(self) -> bool:
        return True

    def write(self, value: str) -> int:
        encoded = str(value).encode("utf-8", errors="replace")
        remaining = self.max_bytes - len(self._data)
        if remaining > 0:
            self._data.extend(encoded[:remaining])
        if len(encoded) > remaining:
            self.truncated = True
        return len(value)

    def getvalue(self) -> str:
        return self._data.decode("utf-8", errors="replace")


def _write_response(response: dict) -> None:
    payload = json.dumps(response, ensure_ascii=False, default=str)
    sys.__stdout__.write(payload)
    sys.__stdout__.flush()


def _load_tool(file_path: Path, entrypoint: str) -> PythonTool:
    if not file_path.is_file():
        raise FileNotFoundError(f"工具文件不存在：{file_path}")
    _, separator, attribute_name = entrypoint.partition(":")
    if not separator or not attribute_name:
        raise ValueError("工具入口格式无效")

    module_name = f"chatai_user_tool_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError("无法创建用户工具模块加载器")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tool = getattr(module, attribute_name, None)
    if not isinstance(tool, PythonTool):
        raise TypeError("工具入口没有导出 PythonTool 实例")
    return tool


def _require_file_integrity(file_path: Path, expected_sha256: str) -> None:
    if not expected_sha256:
        return
    actual_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("工具文件完整性校验失败")


def _require_expected_tool(tool: PythonTool, payload: dict) -> None:
    expected_name = str(payload.get("expected_name", ""))
    if tool.name != expected_name:
        raise ValueError("运行时工具名称与数据库记录不一致")


def _limit_result(data: dict, max_output_bytes: int) -> dict:
    encoded = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    if len(encoded) <= max_output_bytes:
        return data
    return {
        "truncated": True,
        "original_bytes": len(encoded),
        "content": encoded[:max_output_bytes].decode("utf-8", errors="ignore"),
    }


async def _execute(tool: PythonTool, payload: dict) -> dict:
    raw_context = payload.get("context") or {}
    arguments = tool.args_model.model_validate(payload.get("arguments") or {})
    context = ToolContext(
        user_id=int(raw_context["user_id"]),
        conversation_id=raw_context.get("conversation_id"),
        allowed_roots=tuple(
            Path(str(root)) for root in raw_context.get("allowed_roots", [])
        ),
    )
    result = await tool.execute(context, arguments)
    if not isinstance(result, dict):
        raise TypeError("用户工具 execute 必须返回 dict")
    return _limit_result(result, max(1, int(payload["max_output_bytes"])))


def main() -> int:
    stdout_capture = LimitedTextBuffer(8192)
    stderr_capture = LimitedTextBuffer(8192)
    try:
        payload = json.loads(sys.stdin.read())
        file_path = Path(str(payload["file_path"])).resolve(strict=True)
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(
            stderr_capture
        ):
            _require_file_integrity(
                file_path,
                str(payload.get("expected_sha256", "")),
            )
            tool = _load_tool(file_path, str(payload["entrypoint"]))
            _require_expected_tool(tool, payload)
            operation = payload.get("operation")
            if operation == "probe":
                definition = tool.definition()
                result = {
                    "input_schema": definition.input_schema,
                    "name": definition.name,
                    "display_name": definition.display_name,
                    "description": definition.description,
                    "platform": definition.platform,
                }
            elif operation == "execute":
                result = asyncio.run(_execute(tool, payload))
            else:
                raise ValueError("不支持的用户工具运行操作")
        _write_response(
            {
                "ok": True,
                "data": result,
                "captured_stdout": stdout_capture.getvalue(),
                "captured_stderr": stderr_capture.getvalue(),
                "logs_truncated": stdout_capture.truncated or stderr_capture.truncated,
            }
        )
        return 0
    except Exception as exc:
        _write_response(
            {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "captured_stdout": stdout_capture.getvalue(),
                "captured_stderr": stderr_capture.getvalue(),
                "logs_truncated": stdout_capture.truncated or stderr_capture.truncated,
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
