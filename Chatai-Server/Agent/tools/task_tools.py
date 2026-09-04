import asyncio
import os
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Config.config import config


@dataclass(frozen=True, slots=True)
class RegisteredTask:
    task_id: str
    display_name: str
    description: str
    arguments: tuple[str, ...]
    timeout_seconds: int


REGISTERED_TASKS = {
    "chatai_compile_check": RegisteredTask(
        task_id="chatai_compile_check",
        display_name="Chatai Python 编译检查",
        description="使用当前 Python 解释器对后端主要模块执行 compileall 语法编译检查。",
        arguments=("-m", "compileall", "-q", "Agent", "Auth", "Data", "Model", "Server", "System"),
        timeout_seconds=120,
    ),
    "chatai_agent_tests": RegisteredTask(
        task_id="chatai_agent_tests",
        display_name="Chatai Agent 单元测试",
        description="使用当前 Python 解释器运行 Agent/tests 下的 unittest 测试。",
        arguments=("-m", "unittest", "discover", "-s", "Agent/tests", "-p", "test_*.py"),
        timeout_seconds=300,
    ),
}


@dataclass(slots=True)
class TaskRun:
    run_id: str
    user_id: int
    conversation_id: int | None
    task: RegisteredTask
    process: subprocess.Popen
    log_path: Path
    timed_out: bool = False


class RegisteredTaskStore:
    def __init__(self):
        self._runs: dict[str, TaskRun] = {}
        self._lock = threading.Lock()

    def start(self, context: ToolContext, task: RegisteredTask) -> TaskRun:
        with self._lock:
            active = sum(run.process.poll() is None for run in self._runs.values())
            if active >= 4:
                raise RuntimeError("同时运行的注册任务数量已达到上限")
            while len(self._runs) >= 100:
                completed = next((key for key, run in self._runs.items() if run.process.poll() is not None), None)
                if completed is None:
                    break
                self._runs.pop(completed)

            run_id = uuid.uuid4().hex
            log_dir = config.log_path / "agent_tasks"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"{run_id}.log"
            environment = os.environ.copy()
            environment["PYTHONIOENCODING"] = "utf-8"
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            with log_path.open("wb") as output:
                process = subprocess.Popen(
                    [sys.executable, *task.arguments],
                    cwd=config.main_path,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    env=environment,
                    creationflags=creation_flags,
                    start_new_session=os.name != "nt",
                )
            run = TaskRun(run_id, context.user_id, context.conversation_id, task, process, log_path)
            self._runs[run_id] = run
            threading.Thread(target=self._monitor, args=(run,), daemon=True).start()
            return run

    @staticmethod
    def _monitor(run: TaskRun) -> None:
        try:
            run.process.wait(timeout=run.task.timeout_seconds)
        except subprocess.TimeoutExpired:
            run.timed_out = True
            run.process.terminate()
            try:
                run.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                run.process.kill()

    def get(self, run_id: str, context: ToolContext) -> TaskRun:
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            raise ValueError("注册任务运行记录不存在或服务已经重启")
        if run.user_id != context.user_id or run.conversation_id != context.conversation_id:
            raise ValueError("任务运行记录不属于当前用户或会话")
        return run


registered_task_store = RegisteredTaskStore()


class EmptyTaskArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunRegisteredTaskArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: Literal["chatai_compile_check", "chatai_agent_tests"]


class GetTaskStatusArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_run_id: str = Field(min_length=32, max_length=32)
    max_output_chars: int = Field(default=20_000, ge=0, le=65_536)


class ListRegisteredTasksTool(PythonTool[EmptyTaskArguments]):
    name = "list_registered_tasks"
    display_name = "列出注册任务"
    description = "列出后端管理员在代码中预先定义的 Python 测试和编译任务。"
    args_model = EmptyTaskArguments
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: EmptyTaskArguments) -> dict:
        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "display_name": task.display_name,
                    "description": task.description,
                    "timeout_seconds": task.timeout_seconds,
                }
                for task in REGISTERED_TASKS.values()
            ]
        }


class RunRegisteredTaskTool(PythonTool[RunRegisteredTaskArguments]):
    name = "run_registered_task"
    display_name = "运行注册任务"
    description = "运行后端预定义的 Python 任务；只接受 task_id，不接受命令、参数或可执行路径。"
    args_model = RunRegisteredTaskArguments
    risk_level = "medium"
    requires_confirmation = True
    timeout_seconds = 15
    max_output_bytes = 16_384

    async def execute(self, context: ToolContext, arguments: RunRegisteredTaskArguments) -> dict:
        task = REGISTERED_TASKS.get(arguments.task_id)
        if task is None:
            raise ValueError(f"注册任务不存在：{arguments.task_id}")
        run = registered_task_store.start(context, task)
        return {
            "task_run_id": run.run_id,
            "task_id": task.task_id,
            "status": "running",
            "timeout_seconds": task.timeout_seconds,
        }


class GetTaskStatusTool(PythonTool[GetTaskStatusArguments]):
    name = "get_task_status"
    display_name = "查询任务状态"
    description = "查询当前用户和会话启动的注册任务状态及有限日志尾部。"
    args_model = GetTaskStatusArguments
    risk_level = "medium"
    timeout_seconds = 10
    max_output_bytes = 65_536

    async def execute(self, context: ToolContext, arguments: GetTaskStatusArguments) -> dict:
        run = registered_task_store.get(arguments.task_run_id, context)
        exit_code = run.process.poll()
        if run.timed_out:
            status = "timeout"
        elif exit_code is None:
            status = "running"
        elif exit_code == 0:
            status = "success"
        else:
            status = "failed"
        def read_tail() -> str:
            if not arguments.max_output_chars or not run.log_path.is_file():
                return ""
            with run.log_path.open("rb") as file:
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(max(0, size - arguments.max_output_chars))
                return file.read(arguments.max_output_chars).decode("utf-8", errors="replace")

        output = await asyncio.to_thread(read_tail)
        return {
            "task_run_id": run.run_id,
            "task_id": run.task.task_id,
            "status": status,
            "exit_code": exit_code,
            "output_tail": output,
        }
