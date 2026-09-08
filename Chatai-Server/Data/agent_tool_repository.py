import json
import sqlite3
from typing import Any

from Agent.base import ToolDefinition
from Agent.context import ToolPolicy
from Agent.exceptions import (
    ToolConflictError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRepositoryError,
)
from Agent.user_tools.contract import UserToolUploadMetadata


PUBLIC_TOOL_COLUMNS = """
    id,
    tools_name,
    display_name,
    description,
    source_kind,
    risk_level,
    is_enabled,
    created_at,
    updated_at
"""


class AgentToolRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def sync_definitions(self, definitions: list[ToolDefinition]) -> None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                for definition in definitions:
                    connection.execute(
                        """
                        INSERT INTO agent_tools (
                            tools_name,
                            display_name,
                            description,
                            owner_user_id,
                            source_kind,
                            tool_type,
                            platform,
                            input_schema_json,
                            allowed_roots_json,
                            validation_status,
                            validation_error,
                            is_enabled,
                            requires_confirmation,
                            risk_level,
                            timeout_seconds,
                            max_output_bytes,
                            created_at,
                            updated_at
                        ) VALUES (
                            ?, ?, ?, NULL, 'system', 'python_builtin', ?, ?,
                            '["*"]', 'valid', '', ?, ?, ?, ?, ?,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT(tools_name) DO UPDATE SET
                            display_name = excluded.display_name,
                            description = excluded.description,
                            owner_user_id = NULL,
                            source_kind = 'system',
                            tool_type = 'python_builtin',
                            storage_path = '',
                            entrypoint = '',
                            code_sha256 = '',
                            platform = excluded.platform,
                            input_schema_json = excluded.input_schema_json,
                            requires_confirmation = excluded.requires_confirmation,
                            risk_level = excluded.risk_level,
                            timeout_seconds = excluded.timeout_seconds,
                            max_output_bytes = excluded.max_output_bytes,
                            validation_status = 'valid',
                            validation_error = '',
                            deleted_at = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            definition.name,
                            definition.display_name,
                            definition.description,
                            definition.platform,
                            json.dumps(definition.input_schema, ensure_ascii=False),
                            1,
                            int(definition.requires_confirmation),
                            definition.risk_level,
                            definition.timeout_seconds,
                            definition.max_output_bytes,
                        ),
                    )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise ToolRepositoryError(f"同步 Agent 工具定义失败：{exc}") from exc

    @staticmethod
    def _to_public_tool(row) -> dict:
        item = dict(row)
        item["is_enabled"] = bool(item["is_enabled"])
        item["can_delete"] = item["source_kind"] == "user"
        item["can_update"] = item["source_kind"] == "user"
        item.pop("source_kind", None)
        return item

    def list_tools_page(self, user_id: int, page: int, page_size: int) -> dict:
        page = max(1, page)
        page_size = max(1, min(page_size, 50))
        offset = (page - 1) * page_size

        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                total_row = connection.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM agent_tools
                    WHERE deleted_at IS NULL
                      AND (source_kind = 'system' OR owner_user_id = ?)
                    """,
                    (user_id,),
                ).fetchone()
                rows = connection.execute(
                    f"""
                    SELECT {PUBLIC_TOOL_COLUMNS}
                    FROM agent_tools
                    WHERE deleted_at IS NULL
                      AND (source_kind = 'system' OR owner_user_id = ?)
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, page_size, offset),
                ).fetchall()
            except Exception as exc:
                raise ToolRepositoryError(
                    f"分页查询 Agent 工具失败：{exc}"
                ) from exc

        total = int(total_row["total"]) if total_row else 0
        items = [self._to_public_tool(row) for row in rows]

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_tool_detail(self, user_id: int, tool_id: int) -> dict:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                row = connection.execute(
                    f"""
                    SELECT {PUBLIC_TOOL_COLUMNS}
                    FROM agent_tools
                    WHERE id = ?
                      AND deleted_at IS NULL
                      AND (source_kind = 'system' OR owner_user_id = ?)
                    LIMIT 1
                    """,
                    (tool_id, user_id),
                ).fetchone()
            except Exception as exc:
                raise ToolRepositoryError(
                    f"查询 Agent 工具详情失败：{exc}"
                ) from exc
        if row is None:
            raise ToolNotFoundError("Agent 工具不存在")
        return self._to_public_tool(row)

    def create_user_tool(
        self,
        *,
        user_id: int,
        metadata: UserToolUploadMetadata,
        input_schema: dict,
        storage_path: str,
        entrypoint: str,
        code_sha256: str,
    ) -> dict:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                now = self.db_manager.now_time()
                cursor = connection.execute(
                    """
                    INSERT INTO agent_tools (
                        tools_name,
                        display_name,
                        description,
                        owner_user_id,
                        source_kind,
                        tool_type,
                        platform,
                        executable_path,
                        working_dir,
                        argv_template_json,
                        input_schema_json,
                        allowed_roots_json,
                        storage_path,
                        entrypoint,
                        code_sha256,
                        validation_status,
                        validation_error,
                        is_enabled,
                        requires_confirmation,
                        risk_level,
                        timeout_seconds,
                        max_output_bytes,
                        created_at,
                        updated_at
                    ) VALUES (
                        ?, ?, ?, ?, 'user', 'python_builtin', ?, '', '',
                        '[]', ?, '["*"]',
                        ?, ?, ?, 'valid', '', 0, 1, 'high', 30, 65536, ?, ?
                    )
                    """,
                    (
                        metadata.tools_name,
                        metadata.display_name,
                        metadata.description,
                        user_id,
                        metadata.platform,
                        json.dumps(input_schema, ensure_ascii=False),
                        storage_path,
                        entrypoint,
                        code_sha256,
                        now,
                        now,
                    ),
                )
                row = connection.execute(
                    f"""
                    SELECT {PUBLIC_TOOL_COLUMNS}
                    FROM agent_tools
                    WHERE id = ? AND owner_user_id = ?
                    LIMIT 1
                    """,
                    (cursor.lastrowid, user_id),
                ).fetchone()
                if row is None:
                    raise ToolRepositoryError("创建用户 Agent 工具后无法读取记录")
                connection.commit()
                return self._to_public_tool(row)
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                if "agent_tools.tools_name" in str(exc):
                    raise ToolConflictError(
                        f"工具名称已存在：{metadata.tools_name}"
                    ) from exc
                raise ToolRepositoryError(
                    f"创建用户 Agent 工具失败：{exc}"
                ) from exc
            except Exception as exc:
                connection.rollback()
                if isinstance(exc, (ToolConflictError, ToolRepositoryError)):
                    raise
                raise ToolRepositoryError(
                    f"创建用户 Agent 工具失败：{exc}"
                ) from exc

    def set_user_tool_enabled(
        self,
        user_id: int,
        tool_id: int,
        is_enabled: bool,
        *,
        input_schema: dict | None = None,
    ) -> dict:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                row = connection.execute(
                    """
                    SELECT source_kind, owner_user_id
                    FROM agent_tools
                    WHERE id = ? AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    (tool_id,),
                ).fetchone()
                self._require_user_tool_owner(row, user_id, "修改")
                if input_schema is None:
                    connection.execute(
                        """
                        UPDATE agent_tools
                        SET is_enabled = ?, updated_at = ?
                        WHERE id = ? AND owner_user_id = ?
                        """,
                        (
                            int(is_enabled),
                            self.db_manager.now_time(),
                            tool_id,
                            user_id,
                        ),
                    )
                else:
                    connection.execute(
                        """
                        UPDATE agent_tools
                        SET is_enabled = ?, input_schema_json = ?, updated_at = ?
                        WHERE id = ? AND owner_user_id = ?
                        """,
                        (
                            int(is_enabled),
                            json.dumps(input_schema, ensure_ascii=False),
                            self.db_manager.now_time(),
                            tool_id,
                            user_id,
                        ),
                    )
                connection.commit()
            except (ToolNotFoundError, ToolPermissionError):
                connection.rollback()
                raise
            except Exception as exc:
                connection.rollback()
                raise ToolRepositoryError(
                    f"更新 Agent 工具状态失败：{exc}"
                ) from exc
        return self.get_tool_detail(user_id, tool_id)

    def get_user_tool_runtime_by_id(self, user_id: int, tool_id: int) -> dict:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                row = connection.execute(
                    """
                    SELECT id, tools_name, display_name, description,
                           owner_user_id, source_kind, tool_type, platform,
                           input_schema_json, storage_path, entrypoint,
                           code_sha256, validation_status, timeout_seconds,
                           max_output_bytes
                    FROM agent_tools
                    WHERE id = ?
                      AND owner_user_id = ?
                      AND source_kind = 'user'
                      AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    (tool_id, user_id),
                ).fetchone()
            except Exception as exc:
                raise ToolRepositoryError(
                    f"读取用户 Agent 工具运行配置失败：{exc}"
                ) from exc
        if row is None:
            raise ToolNotFoundError("用户 Agent 工具不存在")
        result = dict(row)
        try:
            result["input_schema"] = json.loads(result.pop("input_schema_json"))
        except json.JSONDecodeError as exc:
            raise ToolRepositoryError("用户工具参数 Schema 不是合法 JSON") from exc
        return result

    def delete_user_tool(self, user_id: int, tool_id: int) -> dict:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                row = connection.execute(
                    """
                    SELECT tools_name, source_kind, owner_user_id, storage_path
                    FROM agent_tools
                    WHERE id = ? AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    (tool_id,),
                ).fetchone()
                self._require_user_tool_owner(row, user_id, "删除")
                now = self.db_manager.now_time()
                connection.execute(
                    """
                    UPDATE agent_tools
                    SET is_enabled = 0, deleted_at = ?, updated_at = ?
                    WHERE id = ? AND owner_user_id = ?
                    """,
                    (now, now, tool_id, user_id),
                )
                connection.commit()
                return {
                    "id": tool_id,
                    "tools_name": row["tools_name"],
                    "storage_path": row["storage_path"],
                }
            except (ToolNotFoundError, ToolPermissionError):
                connection.rollback()
                raise
            except Exception as exc:
                connection.rollback()
                raise ToolRepositoryError(
                    f"删除 Agent 工具失败：{exc}"
                ) from exc

    @staticmethod
    def _require_user_tool_owner(row, user_id: int, operation: str) -> None:
        if row is None:
            raise ToolNotFoundError("Agent 工具不存在")
        if row["source_kind"] == "system":
            raise ToolPermissionError(f"系统内置工具不允许用户{operation}")
        if row["owner_user_id"] != user_id:
            raise ToolNotFoundError("Agent 工具不存在")

    def get_user_tool_policy(self, user_id: int, tool_name: str) -> ToolPolicy | None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                row = connection.execute(
                    """
                    SELECT
                        tool.id AS tool_id,
                        tool.tools_name,
                        tool.display_name,
                        tool.description,
                        tool.tool_type,
                        tool.source_kind,
                        tool.platform,
                        tool.input_schema_json,
                        tool.storage_path,
                        tool.entrypoint,
                        tool.code_sha256,
                        tool.allowed_roots_json,
                        tool.is_enabled,
                        tool.requires_confirmation,
                        tool.risk_level,
                        tool.timeout_seconds,
                        tool.max_output_bytes,
                        binding.id AS binding_id,
                        binding.is_enabled AS binding_is_enabled
                    FROM agent_tools AS tool
                    LEFT JOIN agent_tool_bindings AS binding
                      ON binding.tool_id = tool.id
                     AND binding.user_id = ?
                    WHERE tool.tools_name = ?
                      AND tool.deleted_at IS NULL
                      AND tool.validation_status = 'valid'
                      AND (
                        tool.source_kind = 'system'
                        OR tool.owner_user_id = ?
                      )
                    LIMIT 1
                    """,
                    (user_id, tool_name, user_id),
                ).fetchone()
            except Exception as exc:
                raise ToolRepositoryError(f"读取 Agent 工具策略失败：{exc}") from exc

        if row is None:
            return None

        try:
            roots = json.loads(row["allowed_roots_json"] or "[]")
        except json.JSONDecodeError as exc:
            raise ToolRepositoryError(
                f"工具 {tool_name} 的 allowed_roots_json 不是合法 JSON"
            ) from exc
        if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
            raise ToolRepositoryError(
                f"工具 {tool_name} 的 allowed_roots_json 必须是字符串数组"
            )
        if "*" in roots and roots != ["*"]:
            raise ToolRepositoryError(
                f"工具 {tool_name} 的路径通配符不能和其他路径混用"
            )
        try:
            input_schema = json.loads(row["input_schema_json"] or "{}")
        except json.JSONDecodeError as exc:
            raise ToolRepositoryError(
                f"工具 {tool_name} 的 input_schema_json 不是合法 JSON"
            ) from exc
        if not isinstance(input_schema, dict):
            raise ToolRepositoryError(
                f"工具 {tool_name} 的 input_schema_json 必须是 JSON 对象"
            )

        return ToolPolicy(
            tool_id=row["tool_id"],
            tool_name=row["tools_name"],
            display_name=row["display_name"],
            description=row["description"],
            tool_type=row["tool_type"],
            source_kind=row["source_kind"],
            platform=row["platform"],
            allowed_roots=tuple(roots),
            is_enabled=bool(row["is_enabled"]),
            user_is_bound=row["binding_id"] is not None,
            user_is_enabled=bool(row["binding_is_enabled"]),
            requires_confirmation=bool(row["requires_confirmation"]),
            risk_level=row["risk_level"],
            timeout_seconds=max(1, int(row["timeout_seconds"])),
            max_output_bytes=max(1, int(row["max_output_bytes"])),
            storage_path=row["storage_path"],
            entrypoint=row["entrypoint"],
            code_sha256=row["code_sha256"],
            input_schema=input_schema,
        )

    def list_user_enabled_tool_schemas(self, user_id: int) -> list[dict]:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                rows = connection.execute(
                    """
                    SELECT tools_name, description, input_schema_json
                    FROM agent_tools
                    WHERE is_enabled = 1
                      AND tool_type = 'python_builtin'
                      AND validation_status = 'valid'
                      AND deleted_at IS NULL
                      AND (source_kind = 'system' OR owner_user_id = ?)
                    ORDER BY id ASC
                    """,
                    (user_id,),
                ).fetchall()
            except Exception as exc:
                raise ToolRepositoryError(
                    f"查询已启用 Agent 工具 Schema 失败：{exc}"
                ) from exc

        schemas: list[dict] = []
        for row in rows:
            try:
                parameters = json.loads(row["input_schema_json"] or "{}")
            except json.JSONDecodeError as exc:
                raise ToolRepositoryError(
                    f"工具 {row['tools_name']} 的参数 Schema 不是合法 JSON"
                ) from exc
            if not isinstance(parameters, dict):
                raise ToolRepositoryError(
                    f"工具 {row['tools_name']} 的参数 Schema 必须是 JSON 对象"
                )
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": row["tools_name"],
                        "description": row["description"],
                        "parameters": parameters,
                    },
                }
            )
        return schemas

    def list_user_enabled_tool_names(self, user_id: int) -> set[str]:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                rows = connection.execute(
                    """
                    SELECT tools_name
                    FROM agent_tools
                    WHERE is_enabled = 1
                      AND tool_type = 'python_builtin'
                      AND validation_status = 'valid'
                      AND deleted_at IS NULL
                      AND (source_kind = 'system' OR owner_user_id = ?)
                    """,
                    (user_id,),
                ).fetchall()
            except Exception as exc:
                raise ToolRepositoryError(f"查询已启用 Agent 工具失败：{exc}") from exc
        return {row["tools_name"] for row in rows}

    def set_user_tool_binding(
        self,
        user_id: int,
        tool_name: str,
        is_enabled: bool,
    ) -> None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                tool = connection.execute(
                    """
                    SELECT id, tool_type
                    FROM agent_tools
                    WHERE tools_name = ?
                    LIMIT 1
                    """,
                    (tool_name,),
                ).fetchone()
                if tool is None:
                    raise ToolRepositoryError(f"Agent 工具不存在：{tool_name}")
                if tool["tool_type"] != "python_builtin":
                    raise ToolRepositoryError(
                        f"只允许绑定 Python 工具：{tool_name}"
                    )
                connection.execute(
                    """
                    INSERT INTO agent_tool_bindings (
                        user_id,
                        tool_id,
                        is_enabled,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, tool_id) DO UPDATE SET
                        is_enabled = excluded.is_enabled,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, tool["id"], int(is_enabled)),
                )
                connection.commit()
            except ToolRepositoryError:
                connection.rollback()
                raise
            except Exception as exc:
                connection.rollback()
                raise ToolRepositoryError(f"更新用户 Agent 工具绑定失败：{exc}") from exc

    def create_run(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
        tool_id: int,
        tool_name: str,
        arguments: dict,
        status: str,
        error_message: str | None = None,
        step_index: int = 0,
        message_id: int | None = None,
    ) -> int:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO agent_tool_runs (
                        user_id,
                        conversation_id,
                        message_id,
                        tool_id,
                        tools_name,
                        arguments_json,
                        status,
                        error_message,
                        step_index,
                        started_at,
                        ended_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        conversation_id,
                        message_id,
                        tool_id,
                        tool_name,
                        json.dumps(arguments, ensure_ascii=False, default=str),
                        status,
                        error_message,
                        step_index,
                        self.db_manager.now_time(),
                        self.db_manager.now_time() if status == "denied" else None,
                    ),
                )
                connection.commit()
                return cursor.lastrowid
            except Exception as exc:
                connection.rollback()
                raise ToolRepositoryError(f"创建 Agent 工具运行记录失败：{exc}") from exc

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        result: Any = None,
        error_message: str | None = None,
    ) -> None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                connection.execute(
                    """
                    UPDATE agent_tool_runs
                    SET status = ?,
                        result_json = ?,
                        error_message = ?,
                        ended_at = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        json.dumps(result, ensure_ascii=False, default=str)
                        if result is not None
                        else None,
                        error_message,
                        self.db_manager.now_time(),
                        run_id,
                    ),
                )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                raise ToolRepositoryError(f"更新 Agent 工具运行记录失败：{exc}") from exc
