import asyncio
import csv
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.result_storage import create_name_comparison_result
from Agent.tool_policy import resolve_allowed_path


TargetScope = Literal[
    "top_level_entries",
    "top_level_files",
    "top_level_directories",
    "recursive_files",
    "recursive_directories",
    "recursive_entries",
]
NameMode = Literal["basename", "stem", "relative_path"]


class ComparePathNamesArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_file: str = Field(
        description="每行保存一个待比较名称的UTF-8文本文件路径。"
    )
    target_directory: str = Field(
        description="需要扫描并与文本行比较的目标目录。"
    )
    target_scope: TargetScope = Field(
        default="top_level_entries",
        description=(
            "扫描范围；比较目录直接子项时用top_level_entries，"
            "只比较直接子目录时用top_level_directories。"
        ),
    )
    name_mode: NameMode = Field(
        default="basename",
        description="按完整名称、去扩展名名称或相对路径比较。",
    )
    case_sensitive: bool = False
    display_limit: int = Field(default=20, ge=1, le=20)
    export_full_result: bool = Field(
        default=False,
        description=(
            "用户明确要求全部结果时设为true；完整匹配项写入服务端CSV，"
            "聊天正文仍只返回前display_limit项。"
        ),
    )
    max_reference_lines: int = Field(
        default=1_000_000,
        ge=1,
        le=5_000_000,
    )
    max_scanned_entries: int = Field(
        default=1_000_000,
        ge=1,
        le=5_000_000,
    )


def _portable_basename(value: str) -> str:
    return value.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def _normalize_reference(value: str, mode: NameMode, case_sensitive: bool) -> str:
    normalized = value.strip()
    if mode in {"basename", "stem"}:
        normalized = _portable_basename(normalized)
    if mode == "stem":
        normalized = Path(normalized).stem
    return normalized if case_sensitive else normalized.casefold()


def _normalize_target(
    path: Path,
    root: Path,
    mode: NameMode,
    case_sensitive: bool,
) -> str:
    if mode == "relative_path":
        value = path.relative_to(root).as_posix()
    elif mode == "stem":
        value = path.stem
    else:
        value = path.name
    return value if case_sensitive else value.casefold()


def _iter_target_entries(root: Path, scope: TargetScope) -> Iterator[Path]:
    if scope.startswith("top_level_"):
        try:
            entries = root.iterdir()
            for entry in entries:
                if scope == "top_level_files" and not entry.is_file():
                    continue
                if scope == "top_level_directories" and not entry.is_dir():
                    continue
                yield entry
        except (OSError, PermissionError):
            return
        return

    for directory, directory_names, file_names in os.walk(root):
        directory_names.sort(key=str.casefold)
        file_names.sort(key=str.casefold)
        current = Path(directory)
        if scope in {"recursive_directories", "recursive_entries"}:
            for name in directory_names:
                yield current / name
        if scope in {"recursive_files", "recursive_entries"}:
            for name in file_names:
                yield current / name


class ComparePathNamesTool(PythonTool[ComparePathNamesArguments]):
    name = "compare_path_names"
    display_name = "比较路径名称集合"
    description = (
        "使用Python把文本文件中的逐行名称与目标目录的文件或子目录名称做集合比较，"
        "直接返回扫描数量、重名数量和最多20条样本；不会把原始大列表交给模型。"
        "用户要求全部结果时使用export_full_result生成CSV。"
    )
    args_model = ComparePathNamesArguments
    risk_level = "medium"
    timeout_seconds = 120
    max_output_bytes = 32_768

    async def execute(
        self,
        context: ToolContext,
        arguments: ComparePathNamesArguments,
    ) -> dict:
        reference_file = resolve_allowed_path(
            arguments.reference_file,
            context.allowed_roots,
            must_exist=True,
            require_file=True,
        )
        target_directory = resolve_allowed_path(
            arguments.target_directory,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def compare() -> dict:
            reference_names: set[str] = set()
            reference_lines = 0
            reference_truncated = False
            with reference_file.open("r", encoding="utf-8", errors="replace") as file:
                for line in file:
                    if reference_lines >= arguments.max_reference_lines:
                        reference_truncated = True
                        break
                    value = line.strip()
                    if not value:
                        continue
                    reference_lines += 1
                    reference_names.add(
                        _normalize_reference(
                            value,
                            arguments.name_mode,
                            arguments.case_sensitive,
                        )
                    )

            result_file: Path | None = None
            result_download_url: str | None = None
            temporary_file: Path | None = None
            csv_file = None
            csv_writer = None
            if arguments.export_full_result:
                result_file, result_download_url = (
                    create_name_comparison_result(context.user_id)
                )
                result_directory = result_file.parent
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=".name_comparison_",
                    suffix=".tmp",
                    dir=result_directory,
                )
                os.close(descriptor)
                temporary_file = Path(temporary_name)
                csv_file = temporary_file.open("w", encoding="utf-8-sig", newline="")
                csv_writer = csv.DictWriter(
                    csv_file,
                    fieldnames=["name", "path", "type"],
                )
                csv_writer.writeheader()

            scanned_count = 0
            match_count = 0
            sample_items: list[dict] = []
            target_truncated = False
            try:
                for path in _iter_target_entries(
                    target_directory,
                    arguments.target_scope,
                ):
                    if scanned_count >= arguments.max_scanned_entries:
                        target_truncated = True
                        break
                    scanned_count += 1
                    normalized = _normalize_target(
                        path,
                        target_directory,
                        arguments.name_mode,
                        arguments.case_sensitive,
                    )
                    if normalized not in reference_names:
                        continue
                    item = {
                        "name": path.name,
                        "path": str(path),
                        "type": "directory" if path.is_dir() else "file",
                    }
                    match_count += 1
                    if len(sample_items) < arguments.display_limit:
                        sample_items.append(item)
                    if csv_writer is not None:
                        csv_writer.writerow(item)
            finally:
                if csv_file is not None:
                    csv_file.close()

            if result_file is not None and temporary_file is not None:
                os.replace(temporary_file, result_file)

            result_complete = not reference_truncated and not target_truncated
            warnings: list[str] = []
            if reference_truncated:
                warnings.append("参考文本超过最大行数，本次比较不是完整结果")
            if target_truncated:
                warnings.append("目标目录超过最大扫描条目数，本次比较不是完整结果")

            return {
                "reference_file": str(reference_file),
                "target_directory": str(target_directory),
                "target_scope": arguments.target_scope,
                "name_mode": arguments.name_mode,
                "case_sensitive": arguments.case_sensitive,
                "reference_line_count": reference_lines,
                "reference_unique_count": len(reference_names),
                "scanned_entry_count": scanned_count,
                "match_count": match_count,
                "items": sample_items,
                "displayed_count": len(sample_items),
                "has_more": match_count > len(sample_items),
                "result_complete": result_complete,
                "result_file": str(result_file) if result_file is not None else None,
                "result_download_url": result_download_url,
                "warnings": warnings,
                "display_policy": {
                    "answer_summary_first": True,
                    "max_inline_items": arguments.display_limit,
                    "do_not_repeat_source_data": True,
                    "use_result_file_for_full_list": True,
                },
            }

        return await asyncio.to_thread(compare)
