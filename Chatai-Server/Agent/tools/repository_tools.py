import asyncio
import difflib
import hashlib
import os
import struct
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class RepositoryStatusArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    max_entries: int = Field(default=500, ge=1, le=2000)


class FileDiffArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    left_path: str
    right_path: str
    encoding: str = "utf-8"
    context_lines: int = Field(default=3, ge=0, le=20)
    max_bytes_per_file: int = Field(default=2 * 1024 * 1024, ge=1, le=10 * 1024 * 1024)


def _find_git_directory(start: Path) -> tuple[Path, Path]:
    current = start if start.is_dir() else start.parent
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if marker.is_dir():
            return candidate, marker
        if marker.is_file():
            content = marker.read_text(encoding="utf-8", errors="replace").strip()
            if content.casefold().startswith("gitdir:"):
                git_dir = Path(content.split(":", 1)[1].strip())
                if not git_dir.is_absolute():
                    git_dir = (candidate / git_dir).resolve()
                return candidate, git_dir
    raise ValueError(f"路径不属于 Git 工作区：{start}")


def _read_index(index_path: Path) -> dict[str, str]:
    data = index_path.read_bytes()
    if len(data) < 12 or data[:4] != b"DIRC":
        raise ValueError("Git index 文件格式无效")
    version, count = struct.unpack(">II", data[4:12])
    if version not in {2, 3}:
        raise ValueError(f"当前纯 Python 解析器只支持 Git index v2/v3，实际为 v{version}")
    offset = 12
    entries: dict[str, str] = {}
    for _ in range(count):
        entry_start = offset
        if offset + 62 > len(data):
            raise ValueError("Git index 条目不完整")
        object_id = data[offset + 40: offset + 60].hex()
        flags = struct.unpack(">H", data[offset + 60: offset + 62])[0]
        offset += 62
        if version == 3 and flags & 0x4000:
            offset += 2
        name_end = data.find(b"\0", offset)
        if name_end < 0:
            raise ValueError("Git index 路径缺少结束符")
        path = data[offset:name_end].decode("utf-8", errors="surrogateescape")
        entries[path.replace("\\", "/")] = object_id
        consumed = name_end + 1 - entry_start
        offset = entry_start + ((consumed + 7) // 8) * 8
    return entries


def _git_blob_hash(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class GetRepositoryStatusTool(PythonTool[RepositoryStatusArguments]):
    name = "get_repository_status"
    display_name = "查看代码仓库状态"
    description = "使用纯 Python 比较 Git index 和工作区，返回修改、删除及未跟踪路径；不执行 git 命令且不解析 .gitignore。"
    args_model = RepositoryStatusArguments
    timeout_seconds = 60
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: RepositoryStatusArguments) -> dict:
        requested = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True)
        root, git_dir = _find_git_directory(requested)
        root = resolve_allowed_path(str(root), context.allowed_roots, must_exist=True, require_directory=True)
        git_dir = resolve_allowed_path(str(git_dir), context.allowed_roots, must_exist=True, require_directory=True)

        def status() -> dict:
            index_path = git_dir / "index"
            if not index_path.is_file():
                raise ValueError("Git 仓库不存在可读取的 index")
            tracked = _read_index(index_path)
            modified: list[str] = []
            deleted: list[str] = []
            for relative, object_id in tracked.items():
                path = root / Path(relative)
                if not path.exists():
                    deleted.append(relative)
                elif path.is_symlink():
                    modified.append(relative)
                elif path.is_file() and _git_blob_hash(path) != object_id:
                    modified.append(relative)

            tracked_names = set(tracked)
            untracked: list[str] = []
            excluded_directories = {".git", ".venv", "venv", "node_modules", "__pycache__"}
            for directory, directory_names, file_names in os.walk(root, followlinks=False):
                current = Path(directory)
                directory_names[:] = [
                    name for name in directory_names
                    if name not in excluded_directories and not (current / name).is_symlink()
                ]
                for file_name in file_names:
                    path = current / file_name
                    if path.is_symlink():
                        continue
                    relative = path.relative_to(root).as_posix()
                    if relative not in tracked_names:
                        untracked.append(relative)
                        if len(untracked) >= arguments.max_entries:
                            break
                if len(untracked) >= arguments.max_entries:
                    break
            modified.sort()
            deleted.sort()
            untracked.sort()
            total = len(modified) + len(deleted) + len(untracked)
            remaining = arguments.max_entries
            modified_result = modified[:remaining]
            remaining -= len(modified_result)
            deleted_result = deleted[:remaining]
            remaining -= len(deleted_result)
            untracked_result = untracked[:remaining]
            return {
                "repository": str(root),
                "tracked_count": len(tracked),
                "modified": modified_result,
                "deleted": deleted_result,
                "untracked": untracked_result,
                "total_changes": total,
                "truncated": total > arguments.max_entries,
                "limitations": [
                    "不报告暂存区相对 HEAD 的差异",
                    "不解析 .gitignore",
                    "默认跳过 .venv、venv、node_modules 和 __pycache__",
                ],
            }

        return await asyncio.to_thread(status)


class GetFileDiffTool(PythonTool[FileDiffArguments]):
    name = "get_file_diff"
    display_name = "比较文本文件差异"
    description = "使用 Python difflib 比较两个允许范围内文本文件并返回 unified diff。"
    args_model = FileDiffArguments
    risk_level = "medium"
    timeout_seconds = 20
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: FileDiffArguments) -> dict:
        left = resolve_allowed_path(arguments.left_path, context.allowed_roots, must_exist=True, require_file=True)
        right = resolve_allowed_path(arguments.right_path, context.allowed_roots, must_exist=True, require_file=True)
        if left.stat().st_size > arguments.max_bytes_per_file or right.stat().st_size > arguments.max_bytes_per_file:
            raise ValueError("文件大小超过 max_bytes_per_file 限制")

        def compare() -> dict:
            left_lines = left.read_text(encoding=arguments.encoding, errors="replace").splitlines(keepends=True)
            right_lines = right.read_text(encoding=arguments.encoding, errors="replace").splitlines(keepends=True)
            diff = "".join(difflib.unified_diff(
                left_lines,
                right_lines,
                fromfile=str(left),
                tofile=str(right),
                n=arguments.context_lines,
            ))
            return {"left_path": str(left), "right_path": str(right), "same": not diff, "diff": diff}

        return await asyncio.to_thread(compare)
