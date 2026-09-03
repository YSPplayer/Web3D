import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys

from Agent.exceptions import ToolRuntimeError, ToolStorageError, ToolValidationError
from Agent.user_tools.contract import UserToolUploadMetadata, ValidationReport
from Agent.user_tools.process_executor import UserToolProcessExecutor
from Agent.user_tools.storage import StagedTool, StoredTool, UserToolStorage
from Config.config import config


MAX_TOOL_FILE_BYTES = 256 * 1024
MAX_DISPLAY_NAME_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 1000
TOOL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
ALLOWED_PLATFORMS = {"all", "windows", "linux"}


class UserToolUploadService:
    def __init__(
        self,
        repository,
        storage: UserToolStorage | None = None,
        process_executor: UserToolProcessExecutor | None = None,
    ):
        self.repository = repository
        self.storage = storage or UserToolStorage(config.user_agent_tools_path)
        self.process_executor = process_executor or UserToolProcessExecutor(
            self.storage.root_path
        )

    async def upload(
        self,
        *,
        user_id: int,
        original_filename: str,
        content: bytes,
        metadata: UserToolUploadMetadata,
    ) -> dict:
        self._validate_upload(original_filename, content, metadata)
        staged: StagedTool | None = None
        stored: StoredTool | None = None
        try:
            staged = await asyncio.to_thread(self.storage.stage, user_id, content)
            report = await asyncio.to_thread(
                self._validate_in_worker,
                staged.file_path,
                metadata,
            )
            if not report.valid:
                raise ToolValidationError(list(report.errors))
            try:
                input_schema = await self.process_executor.probe(
                    staged.file_path,
                    metadata,
                    report.entrypoint,
                )
            except ToolRuntimeError as exc:
                raise ToolValidationError([str(exc)]) from exc
            stored = await asyncio.to_thread(self.storage.commit, user_id, staged)
            staged = None
            code_sha256 = hashlib.sha256(content).hexdigest()
            try:
                return await asyncio.to_thread(
                    self.repository.create_user_tool,
                    user_id=user_id,
                    metadata=metadata,
                    input_schema=input_schema,
                    storage_path=stored.relative_file_path,
                    entrypoint=report.entrypoint,
                    code_sha256=code_sha256,
                )
            except Exception:
                await asyncio.to_thread(self.storage.cleanup_stored, stored)
                raise
        finally:
            await asyncio.to_thread(self.storage.cleanup_staged, staged)

    @staticmethod
    def _validate_upload(
        original_filename: str,
        content: bytes,
        metadata: UserToolUploadMetadata,
    ) -> None:
        errors: list[str] = []
        if not original_filename.lower().endswith(".py"):
            errors.append("只允许上传 .py 文件")
        if not content:
            errors.append("工具文件不能为空")
        if len(content) > MAX_TOOL_FILE_BYTES:
            errors.append(f"工具文件不能超过 {MAX_TOOL_FILE_BYTES} 字节")
        if not TOOL_NAME_PATTERN.fullmatch(metadata.tools_name):
            errors.append("工具名称必须是 3-64 位小写字母、数字或下划线")
        if not metadata.display_name.strip():
            errors.append("显示名称不能为空")
        elif len(metadata.display_name) > MAX_DISPLAY_NAME_LENGTH:
            errors.append(f"显示名称不能超过 {MAX_DISPLAY_NAME_LENGTH} 个字符")
        if not metadata.description.strip():
            errors.append("工具描述不能为空")
        elif len(metadata.description) > MAX_DESCRIPTION_LENGTH:
            errors.append(f"工具描述不能超过 {MAX_DESCRIPTION_LENGTH} 个字符")
        if metadata.platform not in ALLOWED_PLATFORMS:
            errors.append("platform 只能是 all、windows 或 linux")
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError:
            errors.append("工具文件必须使用 UTF-8 编码")
        if errors:
            raise ToolValidationError(errors)

    @staticmethod
    def _validate_in_worker(
        file_path,
        metadata: UserToolUploadMetadata,
    ) -> ValidationReport:
        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "Agent.user_tools.validation_worker",
                    str(file_path),
                ],
                input=json.dumps(metadata.to_dict(), ensure_ascii=False),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                cwd=config.main_path,
                env=environment,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolValidationError(["工具静态校验超时"]) from exc
        except Exception as exc:
            raise ToolStorageError(f"无法启动工具校验进程：{exc}") from exc

        try:
            output = json.loads(result.stdout.strip())
            report = ValidationReport.from_dict(output)
        except Exception as exc:
            raise ToolStorageError(
                "工具校验进程没有返回合法 JSON"
            ) from exc
        if result.returncode != 0 and report.valid:
            raise ToolStorageError("工具校验进程异常退出")
        return report
