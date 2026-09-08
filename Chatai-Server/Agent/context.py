from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ToolContext:
    user_id: int
    conversation_id: int | None
    allowed_roots: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    tool_id: int
    tool_name: str
    display_name: str
    description: str
    tool_type: str
    source_kind: str
    platform: str
    allowed_roots: tuple[str, ...]
    is_enabled: bool
    user_is_bound: bool
    user_is_enabled: bool
    requires_confirmation: bool
    risk_level: str
    timeout_seconds: int
    max_output_bytes: int
    storage_path: str
    entrypoint: str
    code_sha256: str
    input_schema: dict
