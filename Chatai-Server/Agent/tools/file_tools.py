import asyncio
import fnmatch
import os
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class PathArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str


class ListDirectoryArguments(PathArguments):
    max_depth: int = Field(default=1, ge=0, le=3)


class ReadTextFileArguments(PathArguments):
    encoding: str = "utf-8"
    max_bytes: int = Field(default=20_000, ge=1, le=65_536)


class ReadLinesArguments(PathArguments):
    lines: int = Field(default=50, ge=1, le=200)
    encoding: str = "utf-8"


class FindFilesArguments(PathArguments):
    pattern: str = Field(min_length=1)
    max_results: int = Field(default=50, ge=1, le=200)


class SearchTextArguments(PathArguments):
    pattern: str = Field(min_length=1)
    case_sensitive: bool = False
    max_results: int = Field(default=20, ge=1, le=100)


class DiskUsageArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = ""


class DirectorySizeArguments(PathArguments):
    max_depth: int = Field(default=3, ge=0, le=5)


def _entry_info(path: Path, root: Path) -> dict:
    try:
        stat = path.stat()
        size = stat.st_size if path.is_file() else None
        modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    except OSError:
        size = None
        modified_at = None
    return {
        "name": path.name,
        "path": str(path),
        "relative_path": str(path.relative_to(root)),
        "type": "directory" if path.is_dir() else "file",
        "size_bytes": size,
        "modified_at": modified_at,
    }


class ListDirectoryTool(PythonTool[ListDirectoryArguments]):
    name = "list_directory"
    display_name = "列出目录"
    description = "使用 Python 列出允许目录中的文件和子目录。"
    args_model = ListDirectoryArguments
    timeout_seconds = 10

    async def execute(self, context: ToolContext, arguments: ListDirectoryArguments) -> dict:
        root = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def scan() -> dict:
            entries: list[dict] = []
            truncated = False
            maximum_entries = 1_000

            def visit(directory: Path, depth: int) -> None:
                nonlocal truncated
                if truncated:
                    return
                try:
                    children = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
                except (OSError, PermissionError):
                    return
                for child in children:
                    entries.append(_entry_info(child, root))
                    if len(entries) >= maximum_entries:
                        truncated = True
                        return
                    if child.is_dir() and depth < arguments.max_depth:
                        visit(child, depth + 1)

            visit(root, 0)
            return {
                "path": str(root),
                "entries": entries,
                "truncated": truncated,
            }

        return await asyncio.to_thread(scan)


class FileStatTool(PythonTool[PathArguments]):
    name = "file_stat"
    display_name = "查看文件信息"
    description = "使用 Python 查询允许路径的类型、大小和修改时间。"
    args_model = PathArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: PathArguments) -> dict:
        path = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
        )

        def stat_path() -> dict:
            stat = path.stat()
            return {
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(timespec="seconds"),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "is_symlink": path.is_symlink(),
            }

        return await asyncio.to_thread(stat_path)


class ReadTextFileTool(PythonTool[ReadTextFileArguments]):
    name = "read_text_file"
    display_name = "读取文本文件"
    description = "使用 Python 读取允许目录中的文本文件，并限制最大字节数。"
    args_model = ReadTextFileArguments
    risk_level = "medium"
    timeout_seconds = 10

    async def execute(self, context: ToolContext, arguments: ReadTextFileArguments) -> dict:
        path = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )

        def read_file() -> dict:
            with path.open("rb") as file:
                payload = file.read(arguments.max_bytes + 1)
            truncated = len(payload) > arguments.max_bytes
            payload = payload[: arguments.max_bytes]
            return {
                "path": str(path),
                "encoding": arguments.encoding,
                "content": payload.decode(arguments.encoding, errors="replace"),
                "truncated": truncated,
            }

        return await asyncio.to_thread(read_file)


class ReadFileHeadTool(PythonTool[ReadLinesArguments]):
    name = "read_file_head"
    display_name = "读取文件开头"
    description = "使用 Python 读取允许文本文件的前 N 行。"
    args_model = ReadLinesArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: ReadLinesArguments) -> dict:
        path = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )

        def read_head() -> dict:
            content: list[str] = []
            with path.open("r", encoding=arguments.encoding) as file:
                for _, line in zip(range(arguments.lines), file):
                    content.append(line.rstrip("\r\n"))
            return {"path": str(path), "lines": content}

        return await asyncio.to_thread(read_head)


class ReadFileTailTool(PythonTool[ReadLinesArguments]):
    name = "read_file_tail"
    display_name = "读取文件结尾"
    description = "使用 Python 读取允许文本文件的最后 N 行。"
    args_model = ReadLinesArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: ReadLinesArguments) -> dict:
        path = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )

        def read_tail() -> dict:
            with path.open("r", encoding=arguments.encoding) as file:
                content = deque((line.rstrip("\r\n") for line in file), maxlen=arguments.lines)
            return {"path": str(path), "lines": list(content)}

        return await asyncio.to_thread(read_tail)


class FindFilesTool(PythonTool[FindFilesArguments]):
    name = "find_files"
    display_name = "查找文件"
    description = "使用 Python 在允许目录中按文件名通配符查找文件。"
    args_model = FindFilesArguments
    timeout_seconds = 15

    async def execute(self, context: ToolContext, arguments: FindFilesArguments) -> dict:
        root = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def find() -> dict:
            matches: list[str] = []
            for directory, dir_names, file_names in os.walk(root):
                dir_names.sort(key=str.lower)
                for name in sorted(file_names, key=str.lower):
                    if fnmatch.fnmatch(name, arguments.pattern):
                        matches.append(str(Path(directory) / name))
                        if len(matches) >= arguments.max_results:
                            return {"matches": matches, "truncated": True}
            return {"matches": matches, "truncated": False}

        return await asyncio.to_thread(find)


class SearchTextTool(PythonTool[SearchTextArguments]):
    name = "search_text"
    display_name = "搜索文本"
    description = "使用 Python 在允许目录的文本文件中搜索关键字，不调用外部搜索命令。"
    args_model = SearchTextArguments
    risk_level = "medium"
    timeout_seconds = 15

    async def execute(self, context: ToolContext, arguments: SearchTextArguments) -> dict:
        root = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def search() -> dict:
            matches: list[dict] = []
            needle = arguments.pattern if arguments.case_sensitive else arguments.pattern.casefold()
            for directory, dir_names, file_names in os.walk(root):
                dir_names.sort(key=str.lower)
                for name in sorted(file_names, key=str.lower):
                    path = Path(directory) / name
                    try:
                        if path.stat().st_size > 2 * 1024 * 1024:
                            continue
                        with path.open("r", encoding="utf-8") as file:
                            for line_number, line in enumerate(file, start=1):
                                haystack = line if arguments.case_sensitive else line.casefold()
                                if needle in haystack:
                                    matches.append({
                                        "path": str(path),
                                        "line": line_number,
                                        "text": line.rstrip("\r\n")[:500],
                                    })
                                    if len(matches) >= arguments.max_results:
                                        return {"matches": matches, "truncated": True}
                    except (OSError, PermissionError, UnicodeDecodeError):
                        continue
            return {"matches": matches, "truncated": False}

        return await asyncio.to_thread(search)


class GetDiskUsageTool(PythonTool[DiskUsageArguments]):
    name = "get_disk_usage"
    display_name = "查看磁盘空间"
    description = "使用 Python 查询指定路径所在磁盘的容量和可用空间。"
    args_model = DiskUsageArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: DiskUsageArguments) -> dict:
        if arguments.path:
            path = Path(arguments.path).expanduser().resolve(strict=True)
        elif context.allowed_roots:
            path = context.allowed_roots[0].resolve(strict=True)
        else:
            path = Path.cwd().resolve()

        def disk_usage() -> dict:
            total, used, free = shutil.disk_usage(path)
            return {
                "path": str(path),
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "percent": round(used / total * 100, 2) if total else 0,
            }

        return await asyncio.to_thread(disk_usage)


class GetDirectorySizeTool(PythonTool[DirectorySizeArguments]):
    name = "get_directory_size"
    display_name = "查看目录大小"
    description = "使用 Python 统计允许目录在限定深度内的文件大小。"
    args_model = DirectorySizeArguments
    risk_level = "medium"
    timeout_seconds = 30
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: DirectorySizeArguments) -> dict:
        root = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def calculate() -> dict:
            total_bytes = 0
            file_count = 0
            directory_count = 0

            def visit(directory: Path, depth: int) -> None:
                nonlocal total_bytes, file_count, directory_count
                try:
                    with os.scandir(directory) as entries:
                        for entry in entries:
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    total_bytes += entry.stat(follow_symlinks=False).st_size
                                    file_count += 1
                                elif entry.is_dir(follow_symlinks=False):
                                    directory_count += 1
                                    if depth < arguments.max_depth:
                                        visit(Path(entry.path), depth + 1)
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    return

            visit(root, 0)
            return {
                "path": str(root),
                "size_bytes": total_bytes,
                "file_count": file_count,
                "directory_count": directory_count,
                "max_depth": arguments.max_depth,
            }

        return await asyncio.to_thread(calculate)
