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
