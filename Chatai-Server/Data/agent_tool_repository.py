import json
from typing import Any

from Agent.base import ToolDefinition
from Agent.context import ToolPolicy
from Agent.exceptions import ToolRepositoryError


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
                            tool_type,
                            platform,
                            input_schema_json,
                            allowed_roots_json,
                            is_enabled,
                            requires_confirmation,
                            risk_level,
                            timeout_seconds,
                            max_output_bytes,
                            created_at,
                            updated_at
                        ) VALUES (?, ?, ?, 'python_builtin', ?, ?, '["*"]', 1, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT(tools_name) DO UPDATE SET
                            display_name = excluded.display_name,
                            description = excluded.description,
                            tool_type = 'python_builtin',
                            platform = excluded.platform,
                            input_schema_json = excluded.input_schema_json,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            definition.name,
                            definition.display_name,
                            definition.description,
                            definition.platform,
                            json.dumps(definition.input_schema, ensure_ascii=False),
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

    def list_tools_page(self, page: int, page_size: int) -> dict:
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
                    """
                ).fetchone()
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        tools_name,
                        display_name,
                        description,
                        risk_level,
                        is_enabled,
                        created_at,
                        updated_at
                    FROM agent_tools
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (page_size, offset),
                ).fetchall()
            except Exception as exc:
                raise ToolRepositoryError(
                    f"分页查询 Agent 工具失败：{exc}"
                ) from exc

        total = int(total_row["total"]) if total_row else 0
        items = []
        for row in rows:
            item = dict(row)
            item["is_enabled"] = bool(item["is_enabled"])
            items.append(item)

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_user_tool_policy(self, user_id: int, tool_name: str) -> ToolPolicy | None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                row = connection.execute(
                    """
                    SELECT
                        tool.id AS tool_id,
                        tool.tools_name,
                        tool.tool_type,
                        tool.platform,
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
                    LIMIT 1
                    """,
                    (user_id, tool_name),
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

        return ToolPolicy(
            tool_id=row["tool_id"],
            tool_name=row["tools_name"],
            tool_type=row["tool_type"],
            platform=row["platform"],
            allowed_roots=tuple(roots),
            is_enabled=bool(row["is_enabled"]),
            user_is_bound=row["binding_id"] is not None,
            user_is_enabled=bool(row["binding_is_enabled"]),
            requires_confirmation=bool(row["requires_confirmation"]),
            risk_level=row["risk_level"],
            timeout_seconds=max(1, int(row["timeout_seconds"])),
            max_output_bytes=max(1, int(row["max_output_bytes"])),
        )

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
                    """
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
