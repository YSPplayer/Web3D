import sqlite3
import unittest
from pathlib import Path

from Data.schema_migrations import migrate_schema


class SchemaMigrationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            CREATE TABLE users (id INTEGER PRIMARY KEY);
            CREATE TABLE models (id INTEGER PRIMARY KEY);
            CREATE TABLE agent_tools (
                id INTEGER PRIMARY KEY,
                tools_name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE agent_tool_runs (id INTEGER PRIMARY KEY);
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL
            );
            """
        )

    def tearDown(self):
        self.connection.close()

    def test_agent_tool_ownership_columns_are_added_idempotently(self):
        migrate_schema(self.connection)
        migrate_schema(self.connection)

        columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(agent_tools)"
            ).fetchall()
        }
        self.assertTrue(
            {
                "owner_user_id",
                "source_kind",
                "storage_path",
                "entrypoint",
                "code_sha256",
                "validation_status",
                "validation_error",
                "deleted_at",
            }.issubset(columns)
        )

    def test_run_sql_can_open_legacy_agent_tools_before_migration(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(
            """
            CREATE TABLE agent_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tools_name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                tool_type TEXT NOT NULL DEFAULT 'python_builtin',
                platform TEXT NOT NULL DEFAULT 'all',
                executable_path TEXT NOT NULL DEFAULT '',
                working_dir TEXT NOT NULL DEFAULT '',
                argv_template_json TEXT NOT NULL DEFAULT '[]',
                input_schema_json TEXT NOT NULL DEFAULT '{}',
                allowed_roots_json TEXT NOT NULL DEFAULT '["*"]',
                is_enabled INTEGER NOT NULL DEFAULT 1,
                requires_confirmation INTEGER NOT NULL DEFAULT 0,
                risk_level TEXT NOT NULL DEFAULT 'low',
                timeout_seconds INTEGER NOT NULL DEFAULT 30,
                max_output_bytes INTEGER NOT NULL DEFAULT 65536,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        sql_path = Path(__file__).resolve().parents[2] / "Sql" / "run.sql"

        connection.executescript(sql_path.read_text(encoding="utf-8"))
        migrate_schema(connection)
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(agent_tools)")
        }
        connection.close()

        self.assertIn("owner_user_id", columns)
        self.assertIn("deleted_at", columns)
