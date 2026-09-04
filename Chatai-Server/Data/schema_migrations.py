import sqlite3


def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }


def _add_missing_columns(
    connection: sqlite3.Connection,
    table_name: str,
    migrations: dict[str, str],
) -> bool:
    columns = _column_names(connection, table_name)
    if not columns:
        return False
    for column_name, column_type in migrations.items():
        if column_name not in columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )
    return True


def _migrate_models(connection: sqlite3.Connection) -> None:
    _add_missing_columns(
        connection,
        "models",
        {
            "context_window": "INTEGER",
            "max_output_tokens": "INTEGER",
            "safety_margin_tokens": "INTEGER NOT NULL DEFAULT 512",
        },
    )


def _migrate_agent_tools(connection: sqlite3.Connection) -> None:
    table_exists = _add_missing_columns(
        connection,
        "agent_tools",
        {
            "owner_user_id": "INTEGER REFERENCES users(id) ON DELETE CASCADE",
            "source_kind": (
                "TEXT NOT NULL DEFAULT 'system' "
                "CHECK (source_kind IN ('system', 'user'))"
            ),
            "storage_path": "TEXT NOT NULL DEFAULT ''",
            "entrypoint": "TEXT NOT NULL DEFAULT ''",
            "code_sha256": "TEXT NOT NULL DEFAULT ''",
            "validation_status": (
                "TEXT NOT NULL DEFAULT 'valid' "
                "CHECK (validation_status IN ('pending', 'valid', 'invalid'))"
            ),
            "validation_error": "TEXT NOT NULL DEFAULT ''",
            "deleted_at": "TEXT",
        },
    )
    if not table_exists:
        return
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_tools_owner_user_id "
        "ON agent_tools(owner_user_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_tools_source_owner "
        "ON agent_tools(source_kind, owner_user_id)"
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    migration_name = "agent_system_tools_catalog_v1"
    applied = connection.execute(
        "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
        (migration_name,),
    ).fetchone()
    if applied is None:
        columns = _column_names(connection, "agent_tools")
        # 旧版本曾把 Windows 专用 EXE 作为系统工具写入 run.sql。
        # 保留历史运行记录，通过软删除退出当前工具目录。
        if {"is_enabled", "updated_at"}.issubset(columns):
            connection.execute(
                """
                UPDATE agent_tools
                SET is_enabled = 0,
                    validation_status = 'invalid',
                    validation_error = '已退出跨平台系统工具目录',
                    deleted_at = COALESCE(deleted_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE tools_name = 'run_registered_executable'
                  AND source_kind = 'system'
                """
            )
            # 原始 ICMP 在普通服务账号下不稳定；只在首次升级时改为禁用，
            # 后续不覆盖管理员显式调整的状态。
            connection.execute(
                """
                UPDATE agent_tools
                SET is_enabled = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE tools_name = 'ping_host'
                  AND source_kind = 'system'
                """
            )
        connection.execute(
            "INSERT INTO schema_migrations (migration_name) VALUES (?)",
            (migration_name,),
        )

    retire_x3p_migration = "retire_non_generic_x3p_tools_v1"
    x3p_retired = connection.execute(
        "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
        (retire_x3p_migration,),
    ).fetchone()
    if x3p_retired is None:
        columns = _column_names(connection, "agent_tools")
        required_columns = {
            "is_enabled",
            "source_kind",
            "validation_status",
            "validation_error",
            "deleted_at",
            "updated_at",
        }
        if required_columns.issubset(columns):
            # X3P 属于业务专用格式，不再作为通用系统工具提供。这里采用软删除，
            # 避免破坏历史 agent_tool_runs 记录与外键关系。
            connection.execute(
                """
                UPDATE agent_tools
                SET is_enabled = 0,
                    validation_status = 'invalid',
                    validation_error = '已退出通用系统工具目录',
                    deleted_at = COALESCE(deleted_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE tools_name IN ('inspect_x3p_metadata', 'validate_x3p_file')
                  AND source_kind = 'system'
                """
            )
        connection.execute(
            "INSERT INTO schema_migrations (migration_name) VALUES (?)",
            (retire_x3p_migration,),
        )


def _migrate_agent_tool_runs(connection: sqlite3.Connection) -> None:
    table_exists = _add_missing_columns(
        connection,
        "agent_tool_runs",
        {
            "message_id": "INTEGER",
            "step_index": "INTEGER NOT NULL DEFAULT 0",
        },
    )
    if not table_exists:
        return
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_tool_runs_message_id "
        "ON agent_tool_runs(message_id)"
    )


def _migrate_messages(connection: sqlite3.Connection) -> None:
    table_exists = _add_missing_columns(
        connection,
        "messages",
        {
            "status": "TEXT NOT NULL DEFAULT 'completed'",
            "finish_reason": "TEXT",
            "request_id": "TEXT",
            "updated_at": "TEXT",
        },
    )
    if not table_exists:
        return
    connection.execute(
        "UPDATE messages SET updated_at = created_at "
        "WHERE updated_at IS NULL"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_request_id "
        "ON messages(request_id) WHERE request_id IS NOT NULL"
    )
    connection.execute(
        "UPDATE messages SET status = 'failed', "
        "finish_reason = 'server_restarted' "
        "WHERE status = 'streaming'"
    )


def migrate_schema(connection: sqlite3.Connection) -> None:
    """对已有 SQLite 数据库执行可重复的增量迁移。"""
    _migrate_models(connection)
    _migrate_agent_tools(connection)
    _migrate_agent_tool_runs(connection)
    _migrate_messages(connection)
