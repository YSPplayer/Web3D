import asyncio
import os
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class ListArchiveArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    max_entries: int = Field(default=200, ge=1, le=1000)


class CreateArchiveArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sources: list[str] = Field(min_length=1, max_length=100)
    destination: str
    format: str = Field(default="zip", pattern="^(zip|tar)$")
    overwrite: bool = False


class ExtractArchiveArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    destination: str
    overwrite: bool = False
    max_entries: int = Field(default=1000, ge=1, le=5000)
    max_total_bytes: int = Field(default=512 * 1024 * 1024, ge=1, le=2 * 1024 * 1024 * 1024)


def _archive_kind(path: Path) -> str:
    if zipfile.is_zipfile(path):
        return "zip"
    if tarfile.is_tarfile(path):
        return "tar"
    raise ValueError("只支持 ZIP 或 TAR 压缩包")


def _safe_member_target(destination: Path, member_name: str) -> Path:
    member = PurePosixPath(member_name.replace("\\", "/"))
    if member.is_absolute() or ".." in member.parts:
        raise ValueError(f"压缩包包含不安全路径：{member_name}")
    target = (destination / Path(*member.parts)).resolve()
    if target != destination and not target.is_relative_to(destination):
        raise ValueError(f"压缩包成员越过目标目录：{member_name}")
    return target


class ListArchiveTool(PythonTool[ListArchiveArguments]):
    name = "list_archive"
    display_name = "查看压缩包目录"
    description = "列出允许范围内 ZIP/TAR 压缩包的有限条目，不执行解压。"
    args_model = ListArchiveArguments
    timeout_seconds = 30

    async def execute(self, context: ToolContext, arguments: ListArchiveArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)

        def list_entries() -> dict:
            kind = _archive_kind(path)
            entries = []
            total_entries = 0
            if kind == "zip":
                with zipfile.ZipFile(path) as archive:
                    total_entries = len(archive.infolist())
                    for item in archive.infolist()[: arguments.max_entries]:
                        entries.append({"name": item.filename, "size_bytes": item.file_size, "is_directory": item.is_dir()})
            else:
                with tarfile.open(path) as archive:
                    members = archive.getmembers()
                    total_entries = len(members)
                    for item in members[: arguments.max_entries]:
                        entries.append({"name": item.name, "size_bytes": item.size, "is_directory": item.isdir()})
            return {"path": str(path), "format": kind, "entries": entries, "total_entries": total_entries, "truncated": total_entries > len(entries)}

        return await asyncio.to_thread(list_entries)


class CreateArchiveTool(PythonTool[CreateArchiveArguments]):
    name = "create_archive"
    display_name = "创建压缩包"
    description = "将允许范围内的文件或目录创建为 ZIP/TAR 压缩包。"
    args_model = CreateArchiveArguments
    risk_level = "medium"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: CreateArchiveArguments) -> dict:
        sources = [resolve_allowed_path(value, context.allowed_roots, must_exist=True) for value in arguments.sources]
        destination = resolve_allowed_path(arguments.destination, context.allowed_roots)
        for source in sources:
            if destination == source or (source.is_dir() and destination.is_relative_to(source)):
                raise ValueError("压缩包目标不能位于待归档目录内部")
        if destination.exists() and not arguments.overwrite:
            raise FileExistsError(f"目标已存在：{destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)

        def create() -> dict:
            temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
            try:
                if arguments.format == "zip":
                    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                        for source in sources:
                            if source.is_dir():
                                for child in source.rglob("*"):
                                    if not child.is_symlink() and child.is_file():
                                        archive.write(child, child.relative_to(source.parent))
                            elif not source.is_symlink():
                                archive.write(source, source.name)
                else:
                    with tarfile.open(temporary, "w") as archive:
                        for source in sources:
                            archive.add(source, arcname=source.name, recursive=True)
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
            return {"destination": str(destination), "format": arguments.format, "source_count": len(sources), "size_bytes": destination.stat().st_size}

        return await asyncio.to_thread(create)


class ExtractArchiveTool(PythonTool[ExtractArchiveArguments]):
    name = "extract_archive"
    display_name = "解压文件"
    description = "将 ZIP/TAR 解压到允许目录，并拒绝路径穿越和符号链接成员。"
    args_model = ExtractArchiveArguments
    risk_level = "medium"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: ExtractArchiveArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)
        destination = resolve_allowed_path(arguments.destination, context.allowed_roots)

        def extract() -> dict:
            destination.mkdir(parents=True, exist_ok=True)
            kind = _archive_kind(path)
            extracted = 0
            total_bytes = 0
            if kind == "zip":
                with zipfile.ZipFile(path) as archive:
                    members = archive.infolist()
                    if len(members) > arguments.max_entries:
                        raise ValueError("压缩包条目数量超过限制")
                    total_bytes = sum(item.file_size for item in members)
                    if total_bytes > arguments.max_total_bytes:
                        raise ValueError("压缩包展开大小超过限制")
                    for item in members:
                        target = _safe_member_target(destination, item.filename)
                        mode = (item.external_attr >> 16) & 0o170000
                        if mode == 0o120000:
                            raise ValueError(f"不允许解压符号链接：{item.filename}")
                        if target.exists() and not item.is_dir() and not arguments.overwrite:
                            raise FileExistsError(f"目标文件已存在：{target}")
                    archive.extractall(destination)
                    extracted = len(members)
            else:
                with tarfile.open(path) as archive:
                    members = archive.getmembers()
                    if len(members) > arguments.max_entries:
                        raise ValueError("压缩包条目数量超过限制")
                    total_bytes = sum(item.size for item in members if item.isfile())
                    if total_bytes > arguments.max_total_bytes:
                        raise ValueError("压缩包展开大小超过限制")
                    for item in members:
                        target = _safe_member_target(destination, item.name)
                        if item.issym() or item.islnk():
                            raise ValueError(f"不允许解压链接成员：{item.name}")
                        if target.exists() and item.isfile() and not arguments.overwrite:
                            raise FileExistsError(f"目标文件已存在：{target}")
                    archive.extractall(destination, members=members, filter="data")
                    extracted = len(members)
            return {"path": str(path), "destination": str(destination), "format": kind, "extracted_entries": extracted, "total_bytes": total_bytes}

        return await asyncio.to_thread(extract)
