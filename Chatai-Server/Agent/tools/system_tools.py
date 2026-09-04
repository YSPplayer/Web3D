import getpass
import asyncio
import os
import platform
import socket
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from Agent.base import PythonTool
from Agent.context import ToolContext


class EmptyArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetCurrentTimeTool(PythonTool[EmptyArguments]):
    name = "get_current_time"
    display_name = "获取当前时间"
    description = "获取当前服务器的本地日期、时间、时区和时间戳。"
    args_model = EmptyArguments
    timeout_seconds = 5
    max_output_bytes = 4_096

    async def execute(self, context: ToolContext, arguments: EmptyArguments) -> dict:
        now = datetime.now().astimezone()
        return {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "iso": now.isoformat(timespec="seconds"),
            "timezone": str(now.tzinfo),
            "timestamp": int(now.timestamp()),
        }


class GetHostnameTool(PythonTool[EmptyArguments]):
    name = "get_hostname"
    display_name = "获取主机名"
    description = "获取当前服务器的主机名。"
    args_model = EmptyArguments
    timeout_seconds = 5
    max_output_bytes = 4_096

    async def execute(self, context: ToolContext, arguments: EmptyArguments) -> dict:
        return {"hostname": socket.gethostname()}


class GetCurrentUserTool(PythonTool[EmptyArguments]):
    name = "get_current_user"
    display_name = "获取当前用户"
    description = "获取运行后端服务的操作系统用户名称。"
    args_model = EmptyArguments
    timeout_seconds = 5
    max_output_bytes = 4_096

    async def execute(self, context: ToolContext, arguments: EmptyArguments) -> dict:
        return {"username": getpass.getuser()}


class GetOsInfoTool(PythonTool[EmptyArguments]):
    name = "get_os_info"
    display_name = "获取系统信息"
    description = "获取当前服务器的操作系统、版本、内核和处理器架构。"
    args_model = EmptyArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: EmptyArguments) -> dict:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }


class GetPythonRuntimeInfoTool(PythonTool[EmptyArguments]):
    name = "get_python_runtime_info"
    display_name = "获取 Python 运行环境"
    description = "返回 Python 解释器、实现、版本和虚拟环境状态，不读取环境变量内容。"
    args_model = EmptyArguments
    max_output_bytes = 16_384

    async def execute(self, context: ToolContext, arguments: EmptyArguments) -> dict:
        base_prefix = getattr(sys, "base_prefix", sys.prefix)
        return {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": base_prefix,
            "is_virtual_environment": sys.prefix != base_prefix,
        }


class GetSystemMetricsTool(PythonTool[EmptyArguments]):
    name = "get_system_metrics"
    display_name = "获取系统资源指标"
    description = "返回 CPU、内存和当前工作目录所在磁盘的基础指标，不包含 GPU 厂商专用数据。"
    args_model = EmptyArguments
    timeout_seconds = 10
    max_output_bytes = 16_384

    async def execute(self, context: ToolContext, arguments: EmptyArguments) -> dict:
        try:
            import psutil
        except ImportError as exc:
            raise RuntimeError("系统资源指标工具需要安装 Python 包 psutil") from exc

        def collect() -> dict:
            disk_path = Path.cwd().anchor or os.sep
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(disk_path)
            return {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=0.1),
                    "logical_count": psutil.cpu_count(logical=True),
                    "physical_count": psutil.cpu_count(logical=False),
                },
                "memory": {
                    "percent": memory.percent,
                    "total_bytes": memory.total,
                    "used_bytes": memory.used,
                    "available_bytes": memory.available,
                },
                "disk": {
                    "path": disk_path,
                    "percent": disk.percent,
                    "total_bytes": disk.total,
                    "used_bytes": disk.used,
                    "free_bytes": disk.free,
                },
            }

        return await asyncio.to_thread(collect)
