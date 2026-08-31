import asyncio
import os

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.exceptions import ToolPermissionError

try:
    import psutil
except ImportError:
    psutil = None


class ProcessListArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyword: str = ""
    limit: int = Field(default=50, ge=1, le=100)


class ProcessIdArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pid: int = Field(ge=1)


def _require_psutil():
    if psutil is None:
        raise RuntimeError("进程工具需要安装 Python 包 psutil")
    return psutil


def _safe_process_value(callable_value, process_api, default=None):
    try:
        return callable_value()
    except (
        process_api.NoSuchProcess,
        process_api.AccessDenied,
        process_api.ZombieProcess,
    ):
        return default


class GetProcessListTool(PythonTool[ProcessListArguments]):
    name = "get_process_list"
    display_name = "获取进程列表"
    description = "使用 psutil 获取有限的进程名称、PID、CPU 和内存摘要。"
    args_model = ProcessListArguments
    timeout_seconds = 10

    async def execute(self, context: ToolContext, arguments: ProcessListArguments) -> dict:
        def list_processes() -> dict:
            process_api = _require_psutil()
            keyword = arguments.keyword.casefold().strip()
            result: list[dict] = []
            for process in process_api.process_iter(["pid", "name", "status", "username"]):
                try:
                    info = process.info
                    name = info.get("name") or ""
                    if keyword and keyword not in name.casefold():
                        continue
                    memory = process.memory_info()
                    result.append({
                        "pid": info["pid"],
                        "name": name,
                        "status": info.get("status"),
                        "username": info.get("username"),
                        "cpu_percent": process.cpu_percent(interval=None),
                        "memory_mb": round(memory.rss / 1024 / 1024, 2),
                    })
                    if len(result) >= arguments.limit:
                        break
                except (
                    process_api.NoSuchProcess,
                    process_api.AccessDenied,
                    process_api.ZombieProcess,
                ):
                    continue
            return {"processes": result, "limit": arguments.limit}

        return await asyncio.to_thread(list_processes)


class GetProcessDetailTool(PythonTool[ProcessIdArguments]):
    name = "get_process_detail"
    display_name = "获取进程详情"
    description = "使用 psutil 按 PID 获取进程的基础信息，不返回环境变量。"
    args_model = ProcessIdArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: ProcessIdArguments) -> dict:
        def process_detail() -> dict:
            process_api = _require_psutil()
            process = process_api.Process(arguments.pid)
            memory = process.memory_info()
            return {
                "pid": process.pid,
                "name": _safe_process_value(process.name, process_api),
                "status": _safe_process_value(process.status, process_api),
                "username": _safe_process_value(process.username, process_api),
                "create_time": _safe_process_value(process.create_time, process_api),
                "cpu_percent": _safe_process_value(
                    lambda: process.cpu_percent(interval=None),
                    process_api,
                    0,
                ),
                "memory_mb": round(memory.rss / 1024 / 1024, 2),
                "num_threads": _safe_process_value(process.num_threads, process_api),
            }

        return await asyncio.to_thread(process_detail)


class KillProcessTool(PythonTool[ProcessIdArguments]):
    name = "kill_process"
    display_name = "结束进程"
    description = "使用 psutil 向指定进程发送终止请求；必须由可信的用户确认流程授权。"
    args_model = ProcessIdArguments
    risk_level = "high"
    requires_confirmation = True
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: ProcessIdArguments) -> dict:
        protected_pids = {0, 1, 4, os.getpid(), os.getppid()}
        if arguments.pid in protected_pids:
            raise ToolPermissionError(f"禁止结束受保护进程：{arguments.pid}")

        def terminate() -> dict:
            process_api = _require_psutil()
            process = process_api.Process(arguments.pid)
            name = process.name()
            process.terminate()
            try:
                process.wait(timeout=3)
                terminated = True
            except process_api.TimeoutExpired:
                terminated = False
            return {
                "pid": arguments.pid,
                "name": name,
                "terminated": terminated,
            }

        return await asyncio.to_thread(terminate)
