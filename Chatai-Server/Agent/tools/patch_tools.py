import asyncio
import difflib
import hashlib
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path
from Agent.tools.file_mutation_tools import _atomic_write_text


class PreviewTextPatchArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    new_content: str = Field(max_length=1_000_000)
    encoding: str = "utf-8"
    context_lines: int = Field(default=3, ge=0, le=20)


class ApplyTextPatchArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_token: str = Field(min_length=20, max_length=200)


@dataclass(frozen=True, slots=True)
class PatchOperation:
    user_id: int
    conversation_id: int | None
    path: str
    encoding: str
    base_sha256: str
    new_content: str
    expires_at: float


class PatchOperationStore:
    def __init__(self, ttl_seconds: int = 600, maximum: int = 100):
        self.ttl_seconds = ttl_seconds
        self.maximum = maximum
        self._operations: dict[str, PatchOperation] = {}
        self._lock = threading.Lock()

    def create(self, context: ToolContext, path: Path, encoding: str, base_sha256: str, new_content: str) -> str:
        with self._lock:
            now = time.monotonic()
            self._operations = {
                token: operation
                for token, operation in self._operations.items()
                if operation.expires_at > now
            }
            while len(self._operations) >= self.maximum:
                self._operations.pop(next(iter(self._operations)))
            token = secrets.token_urlsafe(32)
            self._operations[token] = PatchOperation(
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                path=str(path),
                encoding=encoding,
                base_sha256=base_sha256,
                new_content=new_content,
                expires_at=now + self.ttl_seconds,
            )
            return token

    def consume(self, token: str, context: ToolContext) -> PatchOperation:
        with self._lock:
            operation = self._operations.pop(token, None)
        if operation is None:
            raise ValueError("补丁操作令牌不存在或已经使用")
        if operation.expires_at <= time.monotonic():
            raise ValueError("补丁操作令牌已过期")
        if operation.user_id != context.user_id or operation.conversation_id != context.conversation_id:
            raise ValueError("补丁操作令牌不属于当前用户或会话")
        return operation


patch_operation_store = PatchOperationStore()


def _content_hash(content: str, encoding: str) -> str:
    return hashlib.sha256(content.encode(encoding)).hexdigest()


class PreviewTextPatchTool(PythonTool[PreviewTextPatchArguments]):
    name = "preview_text_patch"
    display_name = "预览文本补丁"
    description = "比较文本文件当前内容和候选新内容，返回 unified diff 与短期操作令牌，不修改文件。"
    args_model = PreviewTextPatchArguments
    risk_level = "medium"
    timeout_seconds = 20
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: PreviewTextPatchArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)

        def preview() -> dict:
            current = path.read_text(encoding=arguments.encoding)
            base_sha256 = _content_hash(current, arguments.encoding)
            changed = current != arguments.new_content
            diff = "".join(difflib.unified_diff(
                current.splitlines(keepends=True),
                arguments.new_content.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
                n=arguments.context_lines,
            ))
            token = patch_operation_store.create(
                context,
                path,
                arguments.encoding,
                base_sha256,
                arguments.new_content,
            ) if changed else None
            return {
                "path": str(path),
                "changed": changed,
                "base_sha256": base_sha256,
                "operation_token": token,
                "expires_in_seconds": patch_operation_store.ttl_seconds if token else 0,
                "diff": diff,
            }

        return await asyncio.to_thread(preview)


class ApplyTextPatchTool(PythonTool[ApplyTextPatchArguments]):
    name = "apply_text_patch"
    display_name = "应用文本补丁"
    description = "使用预览阶段签发的短期令牌原子写入文本；令牌绑定用户、会话、路径和原始摘要。"
    args_model = ApplyTextPatchArguments
    risk_level = "medium"
    requires_confirmation = True
    timeout_seconds = 20
    max_output_bytes = 16_384

    async def execute(self, context: ToolContext, arguments: ApplyTextPatchArguments) -> dict:
        operation = patch_operation_store.consume(arguments.operation_token, context)
        path = resolve_allowed_path(operation.path, context.allowed_roots, must_exist=True, require_file=True)

        def apply() -> dict:
            current = path.read_text(encoding=operation.encoding)
            current_sha256 = _content_hash(current, operation.encoding)
            if current_sha256 != operation.base_sha256:
                raise RuntimeError("文件在补丁预览后已经发生变化，请重新生成预览")
            _atomic_write_text(path, operation.new_content, operation.encoding)
            return {
                "path": str(path),
                "applied": True,
                "previous_sha256": operation.base_sha256,
                "current_sha256": _content_hash(operation.new_content, operation.encoding),
            }

        return await asyncio.to_thread(apply)
