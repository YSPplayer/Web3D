import getpass
import platform
import socket
from datetime import datetime

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
