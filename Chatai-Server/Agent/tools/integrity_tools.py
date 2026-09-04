import asyncio
import hashlib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class FileHashArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    algorithm: str = Field(default="sha256", pattern="^(sha256|sha512)$")


class CompareFilesArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    left_path: str
    right_path: str
    algorithm: str = Field(default="sha256", pattern="^(sha256|sha512)$")


def _hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CalculateFileHashTool(PythonTool[FileHashArguments]):
    name = "calculate_file_hash"
    display_name = "计算文件摘要"
    description = "流式计算允许范围内单个文件的 SHA-256 或 SHA-512 摘要。"
    args_model = FileHashArguments
    timeout_seconds = 30
    max_output_bytes = 8_192

    async def execute(self, context: ToolContext, arguments: FileHashArguments) -> dict:
        path = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )
        digest = await asyncio.to_thread(_hash_file, path, arguments.algorithm)
        return {
            "path": str(path),
            "algorithm": arguments.algorithm,
            "digest": digest,
            "size_bytes": path.stat().st_size,
        }


class CompareFilesTool(PythonTool[CompareFilesArguments]):
    name = "compare_files"
    display_name = "比较文件"
    description = "通过文件大小和 SHA-256/SHA-512 摘要判断两个文件是否相同。"
    args_model = CompareFilesArguments
    timeout_seconds = 60
    max_output_bytes = 8_192

    async def execute(self, context: ToolContext, arguments: CompareFilesArguments) -> dict:
        left = resolve_allowed_path(
            arguments.left_path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )
        right = resolve_allowed_path(
            arguments.right_path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )
        left_size = left.stat().st_size
        right_size = right.stat().st_size
        if left_size != right_size:
            return {
                "left_path": str(left),
                "right_path": str(right),
                "same": False,
                "reason": "size_mismatch",
                "left_size_bytes": left_size,
                "right_size_bytes": right_size,
            }
        left_hash, right_hash = await asyncio.gather(
            asyncio.to_thread(_hash_file, left, arguments.algorithm),
            asyncio.to_thread(_hash_file, right, arguments.algorithm),
        )
        return {
            "left_path": str(left),
            "right_path": str(right),
            "same": left_hash == right_hash,
            "algorithm": arguments.algorithm,
            "left_digest": left_hash,
            "right_digest": right_hash,
            "size_bytes": left_size,
        }
