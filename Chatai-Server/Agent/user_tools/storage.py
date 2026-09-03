import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from Agent.exceptions import ToolStorageError


@dataclass(frozen=True, slots=True)
class StagedTool:
    upload_id: str
    directory: Path
    file_path: Path


@dataclass(frozen=True, slots=True)
class StoredTool:
    directory: Path
    file_path: Path
    relative_file_path: str


class UserToolStorage:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.staging_root = self.root_path / "staging"
        self.users_root = self.root_path / "users"

    def stage(self, user_id: int, content: bytes) -> StagedTool:
        upload_id = uuid4().hex
        directory = self.staging_root / str(user_id) / upload_id
        try:
            directory.mkdir(parents=True, exist_ok=False)
            file_path = directory / "tool.py"
            file_path.write_bytes(content)
            return StagedTool(upload_id, directory, file_path)
        except Exception as exc:
            self._remove_directory(directory)
            raise ToolStorageError(f"工具暂存失败：{exc}") from exc

    def commit(self, user_id: int, staged: StagedTool) -> StoredTool:
        destination = self.users_root / str(user_id) / staged.upload_id
        self._require_inside(self.staging_root, staged.directory)
        self._require_inside(self.users_root, destination)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            staged.directory.replace(destination)
            file_path = destination / "tool.py"
            relative_path = file_path.relative_to(self.root_path).as_posix()
            return StoredTool(destination, file_path, relative_path)
        except Exception as exc:
            if not staged.directory.exists():
                self._remove_directory(destination)
            raise ToolStorageError(f"工具正式落盘失败：{exc}") from exc

    def cleanup_staged(self, staged: StagedTool | None) -> None:
        if staged is None:
            return
        self._require_inside(self.staging_root, staged.directory)
        self._remove_directory(staged.directory)

    def cleanup_stored(self, stored: StoredTool | None) -> None:
        if stored is None:
            return
        self._require_inside(self.users_root, stored.directory)
        self._remove_directory(stored.directory)

    @staticmethod
    def _require_inside(root: Path, candidate: Path) -> None:
        try:
            candidate.resolve().relative_to(root.resolve())
        except ValueError as exc:
            raise ToolStorageError("工具文件路径越过了存储根目录") from exc

    @staticmethod
    def _remove_directory(directory: Path) -> None:
        if directory.exists():
            shutil.rmtree(directory)
