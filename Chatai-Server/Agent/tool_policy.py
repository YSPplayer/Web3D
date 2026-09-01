from pathlib import Path

from Agent.exceptions import ToolPermissionError


def resolve_allowed_path(
    raw_path: str,
    allowed_roots: tuple[Path, ...],
    *,
    must_exist: bool = False,
    require_file: bool = False,
    require_directory: bool = False,
) -> Path:
    if not allowed_roots:
        raise ToolPermissionError("当前工具没有配置允许访问的目录")

    root_values = tuple(str(root).strip() for root in allowed_roots)
    allow_all = root_values == ("*",)
    if "*" in root_values and not allow_all:
        raise ToolPermissionError("路径权限配置错误：通配符不能和其他路径混用")

    candidate = Path(raw_path).expanduser().resolve(strict=must_exist)
    if not allow_all:
        permitted = False
        for root in allowed_roots:
            resolved_root = root.expanduser().resolve()
            if candidate == resolved_root or candidate.is_relative_to(resolved_root):
                permitted = True
                break

        if not permitted:
            raise ToolPermissionError(f"路径不在允许范围内：{candidate}")
    if require_file and not candidate.is_file():
        raise ValueError(f"目标不是文件：{candidate}")
    if require_directory and not candidate.is_dir():
        raise ValueError(f"目标不是目录：{candidate}")
    return candidate
