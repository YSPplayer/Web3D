import sqlite3
import unittest
from pathlib import Path

from Data.db_manager import DBManager


class MessageLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.manager = DBManager()
        self.manager.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.manager.conn.row_factory = sqlite3.Row
        self.manager.conn.execute("PRAGMA foreign_keys = ON")
        sql_path = Path(__file__).resolve().parents[2] / "Sql" / "run.sql"
        self.manager.conn.executescript(sql_path.read_text(encoding="utf-8"))
        self.manager.conn.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            ("message_test", "hash"),
        )
        self.manager.conn.execute(
            """
            INSERT INTO model_configs (
                user_id, model_type, model_name, api_key, is_online, is_active
            ) VALUES (1, 'glm', 'glm-4-flash', 'encrypted', 1, 1)
            """
        )
        self.manager.conn.execute(
            """
            INSERT INTO conversations(user_id, model_config_id, title)
            VALUES (1, 1, 'test')
            """
        )
        self.manager.conn.commit()

    def tearDown(self):
        self.manager.close_db()

    def test_cancelled_partial_message_is_saved_and_used_as_context(self):
        created = self.manager.create_messages(
            3,
            1,
            "assistant",
            "",
            status="streaming",
            request_id="request-1",
        )
        finalized = self.manager.finalize_assistant_message(
            created["message_id"],
            "partial answer",
            3,
            "cancelled",
            "user_cancelled",
        )

        self.assertTrue(finalized["updated"])
        row = self.manager.conn.execute(
            "SELECT content, tokens_used, status, finish_reason FROM messages"
        ).fetchone()
        self.assertEqual(row["content"], "partial answer")
        self.assertEqual(row["tokens_used"], 3)
        self.assertEqual(row["status"], "cancelled")
        self.assertEqual(row["finish_reason"], "user_cancelled")
        context = self.manager.get_all_messages_for_context(1)
        self.assertEqual(context[0]["content"], "partial answer")

    def test_empty_failed_message_is_not_used_as_context(self):
        created = self.manager.create_messages(
            3,
            1,
            "assistant",
            "",
            status="streaming",
            request_id="request-2",
        )
        self.manager.finalize_assistant_message(
            created["message_id"],
            "",
            0,
            "failed",
            "provider_error",
        )

        self.assertEqual(self.manager.get_all_messages_for_context(1), [])

    def test_legacy_schema_migration_adds_generation_fields(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(
            """
            CREATE TABLE models(id INTEGER PRIMARY KEY);
            CREATE TABLE agent_tool_runs(id INTEGER PRIMARY KEY);
            CREATE TABLE messages(
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        DBManager._migrate_schema(connection)
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(messages)")
        }
        connection.close()

        self.assertTrue(
            {"status", "finish_reason", "request_id", "updated_at"} <= columns
        )


if __name__ == "__main__":
    unittest.main()
