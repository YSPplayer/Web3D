import asyncio
import fnmatch
import hashlib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class ReadFileRangeArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    start_line: int = Field(default=1, ge=1)
    end_line: int = Field(ge=1)
    encoding: str = "utf-8"
    max_bytes: int = Field(default=65_536, ge=1, le=262_144)


class DirectorySnapshotArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    pattern: str = "*"
    max_depth: int = Field(default=3, ge=0, le=10)
    max_entries: int = Field(default=500, ge=1, le=2000)
    include_hash: bool = False


class SnapshotEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    type: str = Field(pattern="^(file|directory)$")
    size_bytes: int = Field(ge=0)
    modified_ns: int = Field(ge=0)
    sha256: str | None = None


class CompareDirectorySnapshotsArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    before: list[SnapshotEntry] = Field(max_length=2000)
    after: list[SnapshotEntry] = Field(max_length=2000)
    max_results: int = Field(default=500, ge=1, le=2000)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReadFileRangeTool(PythonTool[ReadFileRangeArguments]):
    name = "read_file_range"
    display_name = "读取文件行范围"
    description = "按起止行读取允许范围内文本文件的有限片段；行号从 1 开始。"
    args_model = ReadFileRangeArguments
    risk_level = "medium"
    timeout_seconds = 15
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: ReadFileRangeArguments) -> dict:
        if arguments.end_line < arguments.start_line:
            raise ValueError("end_line 不能小于 start_line")
        if arguments.end_line - arguments.start_line + 1 > 1000:
            raise ValueError("单次最多读取 1000 行")
        path = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )

        def read_range() -> dict:
            lines: list[str] = []
            total_bytes = 0
            truncated = False
            with path.open("r", encoding=arguments.encoding, errors="replace") as file:
                for line_number, line in enumerate(file, start=1):
                    if line_number < arguments.start_line:
                        continue
                    if line_number > arguments.end_line:
                        break
                    encoded_size = len(line.encode(arguments.encoding, errors="replace"))
                    if total_bytes + encoded_size > arguments.max_bytes:
                        truncated = True
                        break
                    lines.append(line.rstrip("\r\n"))
                    total_bytes += encoded_size
            return {
                "path": str(path),
                "start_line": arguments.start_line,
                "end_line": arguments.start_line + len(lines) - 1 if lines else None,
                "lines": lines,
                "truncated": truncated,
            }

        return await asyncio.to_thread(read_range)


class GetDirectorySnapshotTool(PythonTool[DirectorySnapshotArguments]):
    name = "get_directory_snapshot"
    display_name = "获取目录快照"
    description = "返回目录中有限数量条目的相对路径、类型、大小、修改时间及可选摘要。"
    args_model = DirectorySnapshotArguments
    timeout_seconds = 60
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: DirectorySnapshotArguments) -> dict:
        root = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def snapshot() -> dict:
            entries: list[dict] = []
            truncated = False

            def visit(directory: Path, depth: int) -> None:
                nonlocal truncated
                if truncated:
                    return
                try:
                    children = sorted(directory.iterdir(), key=lambda item: item.name.casefold())
                except (OSError, PermissionError):
                    return
                for child in children:
                    if len(entries) >= arguments.max_entries:
                        truncated = True
                        return
                    if child.is_symlink():
                        continue
                    relative = child.relative_to(root).as_posix()
                    if child.is_dir():
                        stat = child.stat()
                        if fnmatch.fnmatch(child.name, arguments.pattern):
                            entries.append({
                                "path": relative,
                                "type": "directory",
                                "size_bytes": 0,
                                "modified_ns": stat.st_mtime_ns,
                                "sha256": None,
                            })
                        if depth < arguments.max_depth:
                            visit(child, depth + 1)
                    elif child.is_file() and fnmatch.fnmatch(child.name, arguments.pattern):
                        stat = child.stat()
                        entries.append({
                            "path": relative,
                            "type": "file",
                            "size_bytes": stat.st_size,
                            "modified_ns": stat.st_mtime_ns,
                            "sha256": _sha256(child) if arguments.include_hash else None,
                        })

            visit(root, 0)
            return {
                "root": str(root),
                "entries": entries,
                "entry_count": len(entries),
                "include_hash": arguments.include_hash,
                "truncated": truncated,
            }

        return await asyncio.to_thread(snapshot)


class CompareDirectorySnapshotsTool(PythonTool[CompareDirectorySnapshotsArguments]):
    name = "compare_directory_snapshots"
    display_name = "比较目录快照"
    description = "比较两份目录快照，返回新增、删除和发生变化的相对路径。"
    args_model = CompareDirectorySnapshotsArguments
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: CompareDirectorySnapshotsArguments) -> dict:
        def comparable(entry: SnapshotEntry) -> tuple:
            return (entry.type, entry.size_bytes, entry.modified_ns, entry.sha256)

        before = {entry.path: entry for entry in arguments.before}
        after = {entry.path: entry for entry in arguments.after}
        added = sorted(after.keys() - before.keys())
        removed = sorted(before.keys() - after.keys())
        modified = sorted(
            path for path in before.keys() & after.keys()
            if comparable(before[path]) != comparable(after[path])
        )
        total = len(added) + len(removed) + len(modified)
        remaining = arguments.max_results
        limited_added = added[:remaining]
        remaining -= len(limited_added)
        limited_removed = removed[:remaining]
        remaining -= len(limited_removed)
        limited_modified = modified[:remaining]
        return {
            "added": limited_added,
            "removed": limited_removed,
            "modified": limited_modified,
            "total_changes": total,
            "truncated": total > arguments.max_results,
        }
