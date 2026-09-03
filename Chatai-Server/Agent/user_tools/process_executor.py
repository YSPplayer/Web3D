import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

from Agent.exceptions import (
    ToolRuntimeError,
    ToolRuntimeOutputError,
    ToolRuntimeTimeoutError,
    ToolValidationError,
)
from Agent.user_tools.contract import UserToolUploadMetadata
from Config.config import config


MAX_PROTOCOL_OVERHEAD_BYTES = 65_536
MAX_DIAGNOSTIC_BYTES = 16_384


class _ProtocolOutputExceeded(Exception):
    pass


class UserToolProcessExecutor:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root.resolve()

    async def probe(
        self,
        file_path: Path,
        metadata: UserToolUploadMetadata,
        entrypoint: str,
        *,
        timeout_seconds: int = 5,
    ) -> dict:
        resolved_path = self._resolve_path(file_path)
        response = await self._run_worker(
            {
                "operation": "probe",
                "file_path": str(resolved_path),
                "entrypoint": entrypoint,
                "expected_name": metadata.tools_name,
                "expected_sha256": hashlib.sha256(
                    resolved_path.read_bytes()
                ).hexdigest(),
            },
            timeout_seconds=timeout_seconds,
            max_stdout_bytes=MAX_PROTOCOL_OVERHEAD_BYTES,
        )
        if not response.get("ok"):
            raise ToolValidationError(
                [f"工具运行时校验失败：{response.get('error', '未知错误')}"]
            )
        definition = response.get("data")
        if not isinstance(definition, dict):
            raise ToolValidationError(["工具运行时没有返回合法定义"])
        expected_values = {
            "name": metadata.tools_name,
            "display_name": metadata.display_name,
            "description": metadata.description,
            "platform": metadata.platform,
        }
        for key, expected in expected_values.items():
            if definition.get(key) != expected:
                raise ToolValidationError([f"工具运行时字段 {key} 与上传表单不一致"])
        input_schema = definition.get("input_schema")
        if not isinstance(input_schema, dict):
            raise ToolValidationError(["工具参数 Schema 必须是 JSON 对象"])
        return input_schema

    async def verify_registered(self, runtime: dict) -> dict:
        metadata = UserToolUploadMetadata(
            tools_name=runtime["tools_name"],
            display_name=runtime["display_name"],
            description=runtime["description"],
            platform=runtime["platform"],
        )
        file_path = self.resolve_storage_path(runtime["storage_path"])
        response = await self._run_worker(
            {
                "operation": "probe",
                "file_path": str(file_path),
                "entrypoint": runtime["entrypoint"],
                "expected_name": runtime["tools_name"],
                "expected_sha256": runtime["code_sha256"],
            },
            timeout_seconds=min(10, max(1, int(runtime["timeout_seconds"]))),
            max_stdout_bytes=MAX_PROTOCOL_OVERHEAD_BYTES,
        )
        if not response.get("ok"):
            raise ToolValidationError(
                [f"工具启用校验失败：{response.get('error', '未知错误')}"]
            )
        definition = response.get("data") or {}
        expected_values = {
            "name": metadata.tools_name,
            "display_name": metadata.display_name,
            "description": metadata.description,
            "platform": metadata.platform,
        }
        if any(
            definition.get(key) != expected
            for key, expected in expected_values.items()
        ):
            raise ToolValidationError(["工具运行时定义与数据库记录不一致"])
        input_schema = definition.get("input_schema")
        if not isinstance(input_schema, dict):
            raise ToolValidationError(["工具参数 Schema 必须是 JSON 对象"])
        return input_schema

    async def execute(
        self,
        *,
        runtime: dict,
        user_id: int,
        conversation_id: int | None,
        allowed_roots: tuple[str, ...],
        arguments: dict,
        timeout_seconds: int,
        max_output_bytes: int,
    ) -> dict:
        file_path = self.resolve_storage_path(runtime["storage_path"])
        response = await self._run_worker(
            {
                "operation": "execute",
                "file_path": str(file_path),
                "entrypoint": runtime["entrypoint"],
                "expected_name": runtime["tools_name"],
                "expected_sha256": runtime["code_sha256"],
                "context": {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "allowed_roots": list(allowed_roots),
                },
                "arguments": arguments,
                "max_output_bytes": max_output_bytes,
            },
            timeout_seconds=timeout_seconds,
            max_stdout_bytes=max_output_bytes + MAX_PROTOCOL_OVERHEAD_BYTES,
        )
        if not response.get("ok"):
            error_type = response.get("error_type", "ToolRuntimeError")
            message = response.get("error", "用户工具执行失败")
            raise ToolRuntimeError(f"{error_type}: {message}")
        data = response.get("data")
        if not isinstance(data, dict):
            raise ToolRuntimeError("用户工具返回的数据不是 JSON 对象")
        return data

    def resolve_storage_path(self, relative_path: str) -> Path:
        if not relative_path:
            raise ToolRuntimeError("用户工具没有配置存储路径")
        return self._resolve_path(self.storage_root / relative_path)

    def _resolve_path(self, file_path: Path) -> Path:
        try:
            resolved = file_path.resolve(strict=True)
            resolved.relative_to(self.storage_root)
        except (FileNotFoundError, ValueError) as exc:
            raise ToolRuntimeError("用户工具文件不存在或越过存储目录") from exc
        if not resolved.is_file():
            raise ToolRuntimeError("用户工具存储路径不是文件")
        return resolved

    async def _run_worker(
        self,
        payload: dict,
        *,
        timeout_seconds: int,
        max_stdout_bytes: int,
    ) -> dict:
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "Agent.user_tools.runtime_worker",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(config.main_path),
                env=self._worker_environment(),
            )
        except OSError as exc:
            raise ToolRuntimeError(f"无法启动用户工具进程：{exc}") from exc
        encoded_input = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            assert process.stdin is not None
            process.stdin.write(encoded_input)
            await process.stdin.drain()
            process.stdin.close()
            stdout_task = asyncio.create_task(
                self._read_limited(process.stdout, max_stdout_bytes)
            )
            stderr_task = asyncio.create_task(
                self._read_limited(process.stderr, MAX_DIAGNOSTIC_BYTES)
            )
            wait_task = asyncio.create_task(process.wait())
            stdout, stderr, return_code = await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task, wait_task),
                timeout=max(1, timeout_seconds),
            )
        except asyncio.TimeoutError as exc:
            await self._terminate(process)
            raise ToolRuntimeTimeoutError(
                f"用户工具执行超过 {timeout_seconds} 秒"
            ) from exc
        except _ProtocolOutputExceeded as exc:
            await self._terminate(process)
            raise ToolRuntimeOutputError("用户工具进程输出超过允许大小") from exc
        except (BrokenPipeError, ConnectionResetError, OSError) as exc:
            await self._terminate(process)
            raise ToolRuntimeError(f"用户工具进程通信失败：{exc}") from exc
        except asyncio.CancelledError:
            await self._terminate(process)
            raise

        if not stdout:
            diagnostic = stderr.decode("utf-8", errors="replace").strip()
            raise ToolRuntimeError(
                f"用户工具进程没有返回结果：{diagnostic or return_code}"
            )
        try:
            response = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ToolRuntimeError("用户工具进程返回了无效 JSON") from exc
        if not isinstance(response, dict):
            raise ToolRuntimeError("用户工具进程返回格式无效")
        return response

    @staticmethod
    async def _read_limited(
        stream: asyncio.StreamReader | None,
        max_bytes: int,
    ) -> bytes:
        if stream is None:
            return b""
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = await stream.read(8192)
            if not chunk:
                return b"".join(chunks)
            total += len(chunk)
            if total > max_bytes:
                raise _ProtocolOutputExceeded
            chunks.append(chunk)

    @staticmethod
    async def _terminate(process: asyncio.subprocess.Process) -> None:
        await asyncio.to_thread(
            UserToolProcessExecutor._terminate_descendants,
            process.pid,
        )
        if process.returncode is None:
            process.kill()
        try:
            await asyncio.wait_for(process.wait(), timeout=2)
        except asyncio.TimeoutError:
            pass

    @staticmethod
    def _terminate_descendants(process_id: int) -> None:
        try:
            import psutil

            parent = psutil.Process(process_id)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            _, alive = psutil.wait_procs(children, timeout=1)
            for child in alive:
                child.kill()
        except ImportError:
            return
        except Exception:
            return

    @staticmethod
    def _worker_environment() -> dict[str, str]:
        keep_names = {
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "HOME",
            "USERPROFILE",
        }
        environment = {
            key: value for key, value in os.environ.items() if key.upper() in keep_names
        }
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment
