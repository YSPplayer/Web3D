import asyncio
import fnmatch
import os
import shutil
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.exceptions import ToolPermissionError
from Agent.tool_policy import resolve_allowed_path


SUPPORTED_ENCODINGS = {"utf-8", "utf-8-sig", "gb18030", "latin-1"}


def _validate_encoding(value: str) -> str:
    normalized = value.casefold()
    if normalized not in SUPPORTED_ENCODINGS:
        raise ValueError(f"不支持的文本编码：{value}")
    return normalized


def _reject_protected_root(path: Path) -> None:
    resolved = path.resolve()
    protected = {Path(resolved.anchor).resolve(), Path.home().resolve(), Path.cwd().resolve()}
    if resolved in protected:
        raise ToolPermissionError(f"禁止直接操作受保护根路径：{resolved}")


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _atomic_write_text(path: Path, content: str, encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding, newline="") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class CreateDirectoryArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    parents: bool = True
    exist_ok: bool = False


class CopyPathArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    destination: str
    overwrite: bool = False


class RenamePathArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    new_name: str = Field(min_length=1, max_length=255)

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value in {".", ".."} or Path(value).name != value or "/" in value or "\\" in value:
            raise ValueError("new_name 只能是单个文件或目录名称")
        return value


class WriteTextArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content: str = Field(max_length=1_000_000)
    encoding: str = "utf-8"
    overwrite: bool = False

    _encoding = field_validator("encoding")(_validate_encoding)


class AppendTextArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content: str = Field(max_length=1_000_000)
    encoding: str = "utf-8"

    _encoding = field_validator("encoding")(_validate_encoding)


class ReplaceTextArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    search: str = Field(min_length=1, max_length=100_000)
    replacement: str = Field(max_length=100_000)
    max_replacements: int = Field(default=100, ge=1, le=10_000)
    encoding: str = "utf-8"

    _encoding = field_validator("encoding")(_validate_encoding)


class MovePathArguments(CopyPathArguments):
    pass


class DeletePathArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    recursive: bool = False
    use_trash: bool = True


class DeleteDirectoryContentsArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    pattern: str = "*"
    max_entries: int = Field(default=200, ge=1, le=1000)


class BulkReplaceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    pattern: str = "*.txt"
    search: str = Field(min_length=1, max_length=100_000)
    replacement: str = Field(max_length=100_000)
    max_files: int = Field(default=20, ge=1, le=200)
    max_replacements_per_file: int = Field(default=100, ge=1, le=10_000)
    encoding: str = "utf-8"

    _encoding = field_validator("encoding")(_validate_encoding)


class CreateDirectoryTool(PythonTool[CreateDirectoryArguments]):
    name = "create_directory"
    display_name = "创建目录"
    description = "在允许范围内创建目录。"
    args_model = CreateDirectoryArguments
    risk_level = "medium"
    requires_confirmation = True

    async def execute(self, context: ToolContext, arguments: CreateDirectoryArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots)
        await asyncio.to_thread(path.mkdir, parents=arguments.parents, exist_ok=arguments.exist_ok)
        return {"path": str(path), "created": True}


class CopyPathTool(PythonTool[CopyPathArguments]):
    name = "copy_path"
    display_name = "复制文件或目录"
    description = "在允许范围内复制文件或目录，不删除源路径。"
    args_model = CopyPathArguments
    risk_level = "medium"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: CopyPathArguments) -> dict:
        source = resolve_allowed_path(arguments.source, context.allowed_roots, must_exist=True)
        destination = resolve_allowed_path(arguments.destination, context.allowed_roots)
        if destination == source or (source.is_dir() and destination.is_relative_to(source)):
            raise ValueError("复制目标不能是源路径本身或源目录的子目录")
        if destination.exists() and not arguments.overwrite:
            raise FileExistsError(f"目标已存在：{destination}")

        def copy() -> None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=arguments.overwrite)
            else:
                shutil.copy2(source, destination)

        await asyncio.to_thread(copy)
        return {"source": str(source), "destination": str(destination), "copied": True}


class RenamePathTool(PythonTool[RenamePathArguments]):
    name = "rename_path"
    display_name = "重命名路径"
    description = "在允许范围内、同一父目录中重命名文件或目录。"
    args_model = RenamePathArguments
    risk_level = "medium"
    requires_confirmation = True

    async def execute(self, context: ToolContext, arguments: RenamePathArguments) -> dict:
        source = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True)
        destination = resolve_allowed_path(str(source.with_name(arguments.new_name)), context.allowed_roots)
        if destination.exists():
            raise FileExistsError(f"目标已存在：{destination}")
        await asyncio.to_thread(source.rename, destination)
        return {"source": str(source), "destination": str(destination), "renamed": True}


class WriteTextFileTool(PythonTool[WriteTextArguments]):
    name = "write_text_file"
    display_name = "写入文本文件"
    description = "使用临时文件和原子替换写入允许范围内的单个文本文件。"
    args_model = WriteTextArguments
    risk_level = "medium"
    requires_confirmation = True

    async def execute(self, context: ToolContext, arguments: WriteTextArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots)
        if path.exists() and not arguments.overwrite:
            raise FileExistsError(f"目标已存在：{path}")
        await asyncio.to_thread(_atomic_write_text, path, arguments.content, arguments.encoding)
        return {"path": str(path), "characters_written": len(arguments.content), "encoding": arguments.encoding}


class AppendTextFileTool(PythonTool[AppendTextArguments]):
    name = "append_text_file"
    display_name = "追加文本"
    description = "向允许范围内的文本文件末尾追加有限长度内容。"
    args_model = AppendTextArguments
    risk_level = "medium"
    requires_confirmation = True

    async def execute(self, context: ToolContext, arguments: AppendTextArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots)
        path.parent.mkdir(parents=True, exist_ok=True)

        def append() -> None:
            with path.open("a", encoding=arguments.encoding, newline="") as file:
                file.write(arguments.content)

        await asyncio.to_thread(append)
        return {"path": str(path), "characters_appended": len(arguments.content), "encoding": arguments.encoding}


class ReplaceTextInFileTool(PythonTool[ReplaceTextArguments]):
    name = "replace_text_in_file"
    display_name = "替换文件文本"
    description = "在允许范围内的单个文本文件中执行有限次数的纯文本替换。"
    args_model = ReplaceTextArguments
    risk_level = "medium"
    requires_confirmation = True

    async def execute(self, context: ToolContext, arguments: ReplaceTextArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)

        def replace() -> int:
            content = path.read_text(encoding=arguments.encoding)
            count = min(content.count(arguments.search), arguments.max_replacements)
            if count:
                _atomic_write_text(path, content.replace(arguments.search, arguments.replacement, arguments.max_replacements), arguments.encoding)
            return count

        count = await asyncio.to_thread(replace)
        return {"path": str(path), "replacements": count}


class MovePathTool(PythonTool[MovePathArguments]):
    name = "move_path"
    display_name = "移动文件或目录"
    description = "移动允许范围内的路径，成功后源路径消失。"
    args_model = MovePathArguments
    risk_level = "high"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: MovePathArguments) -> dict:
        source = resolve_allowed_path(arguments.source, context.allowed_roots, must_exist=True)
        destination = resolve_allowed_path(arguments.destination, context.allowed_roots)
        _reject_protected_root(source)
        if destination == source or (source.is_dir() and destination.is_relative_to(source)):
            raise ValueError("移动目标不能是源路径本身或源目录的子目录")
        if destination.exists():
            if not arguments.overwrite:
                raise FileExistsError(f"目标已存在：{destination}")
            _reject_protected_root(destination)
            await asyncio.to_thread(_remove_path, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.move, str(source), str(destination))
        return {"source": str(source), "destination": str(destination), "moved": True}


class DeletePathTool(PythonTool[DeletePathArguments]):
    name = "delete_path"
    display_name = "删除路径"
    description = "删除允许范围内的单个路径；默认要求送入系统回收站。"
    args_model = DeletePathArguments
    risk_level = "high"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: DeletePathArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True)
        _reject_protected_root(path)
        if path.is_dir() and not path.is_symlink() and not arguments.recursive:
            raise ValueError("删除目录必须显式设置 recursive=true")
        if arguments.use_trash:
            try:
                from send2trash import send2trash
            except ImportError as exc:
                raise RuntimeError("当前环境未安装 send2trash，不能安全送入回收站") from exc
            await asyncio.to_thread(send2trash, str(path))
            deletion_mode = "trash"
        else:
            await asyncio.to_thread(_remove_path, path)
            deletion_mode = "permanent"
        return {"path": str(path), "deleted": True, "mode": deletion_mode}


class DeleteDirectoryContentsTool(PythonTool[DeleteDirectoryContentsArguments]):
    name = "delete_directory_contents"
    display_name = "清空目录内容"
    description = "批量删除允许目录内匹配模式的直接子项，不删除目录本身。"
    args_model = DeleteDirectoryContentsArguments
    risk_level = "high"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: DeleteDirectoryContentsArguments) -> dict:
        root = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_directory=True)
        _reject_protected_root(root)
        targets = [item for item in root.iterdir() if fnmatch.fnmatch(item.name, arguments.pattern)]
        if len(targets) > arguments.max_entries:
            raise ValueError(f"匹配到 {len(targets)} 个条目，超过 max_entries 限制")
        for target in targets:
            await asyncio.to_thread(_remove_path, target)
        return {"path": str(root), "pattern": arguments.pattern, "deleted_count": len(targets)}


class BulkReplaceTextTool(PythonTool[BulkReplaceArguments]):
    name = "bulk_replace_text"
    display_name = "批量替换文本"
    description = "在允许目录内对有限数量的匹配文本文件执行纯文本替换。"
    args_model = BulkReplaceArguments
    risk_level = "high"
    requires_confirmation = True
    timeout_seconds = 120

    async def execute(self, context: ToolContext, arguments: BulkReplaceArguments) -> dict:
        root = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_directory=True)
        paths = [path for path in root.rglob(arguments.pattern) if path.is_file() and not path.is_symlink()]
        if len(paths) > arguments.max_files:
            raise ValueError(f"匹配到 {len(paths)} 个文件，超过 max_files 限制")

        def replace_all() -> list[dict]:
            changed = []
            for path in paths:
                content = path.read_text(encoding=arguments.encoding)
                count = min(content.count(arguments.search), arguments.max_replacements_per_file)
                if count:
                    _atomic_write_text(path, content.replace(arguments.search, arguments.replacement, arguments.max_replacements_per_file), arguments.encoding)
                    changed.append({"path": str(path), "replacements": count})
            return changed

        changed = await asyncio.to_thread(replace_all)
        return {"path": str(root), "matched_files": len(paths), "changed_files": changed}
