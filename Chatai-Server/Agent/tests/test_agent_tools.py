import sqlite3
import threading
import unittest
from pathlib import Path

from Agent.context import ToolContext
from Agent.exceptions import ToolNotFoundError, ToolPermissionError
from Agent.factory import build_default_registry
from Agent.tool_dispatcher import ToolDispatcher
from Agent.tools.file_tools import ListDirectoryArguments, ListDirectoryTool
from Data.agent_tool_repository import AgentToolRepository


class MemoryDbManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.connection = sqlite3.connect(":memory:", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def get_db_connection(self):
        return self.connection

    @staticmethod
    def now_time():
        return "2026-08-31 12:00:00"

    def close(self):
        self.connection.close()


class AgentToolModuleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db_manager = MemoryDbManager()
        sql_path = Path(__file__).resolve().parents[2] / "Sql" / "run.sql"
        self.db_manager.connection.executescript(sql_path.read_text(encoding="utf-8"))
        cursor = self.db_manager.connection.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            ("agent_test", "test_hash"),
        )
        self.user_id = cursor.lastrowid
        cursor = self.db_manager.connection.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            ("other_agent_test", "test_hash"),
        )
        self.other_user_id = cursor.lastrowid
        self.db_manager.connection.commit()

        self.registry = build_default_registry()
        self.repository = AgentToolRepository(self.db_manager)
        self.repository.sync_definitions(self.registry.definitions())

    def create_user_tool(self, owner_user_id: int, tool_name: str) -> int:
        cursor = self.db_manager.connection.execute(
            """
            INSERT INTO agent_tools (
                tools_name,
                display_name,
                description,
                owner_user_id,
                source_kind,
                tool_type,
                platform,
                storage_path,
                entrypoint,
                code_sha256,
                validation_status,
                is_enabled,
                risk_level
            ) VALUES (?, ?, 'test', ?, 'user', 'python_builtin', 'all',
                      ?, 'tool:tool', 'sha256', 'valid', 1, 'low')
            """,
            (
                tool_name,
                tool_name,
                owner_user_id,
                f"users/{owner_user_id}/{tool_name}/tool.py",
            ),
        )
        self.db_manager.connection.commit()
        return cursor.lastrowid

    def tearDown(self):
        self.db_manager.close()

    async def test_enabled_python_tool_can_run_without_binding(self):
        dispatcher = ToolDispatcher(self.registry, self.repository)
        schemas = await dispatcher.model_schemas_for_user(user_id=1)
        schema_names = {schema["function"]["name"] for schema in schemas}

        self.assertIn("get_current_time", schema_names)

        result = await dispatcher.execute(
            user_id=1,
            conversation_id=None,
            tool_name="get_current_time",
            arguments={},
            step_index=2,
        )

        self.assertEqual(result.status, "success")
        self.assertIn("datetime", result.data)
        run = self.db_manager.connection.execute(
            "SELECT status, step_index FROM agent_tool_runs WHERE id = ?",
            (result.run_id,),
        ).fetchone()
        self.assertEqual(run["status"], "success")
        self.assertEqual(run["step_index"], 2)

    async def test_system_disabled_tool_is_denied_and_audited(self):
        self.db_manager.connection.execute(
            "UPDATE agent_tools SET is_enabled = 0 WHERE tools_name = ?",
            ("get_hostname",),
        )
        self.db_manager.connection.commit()
        dispatcher = ToolDispatcher(self.registry, self.repository)

        result = await dispatcher.execute(
            user_id=1,
            conversation_id=None,
            tool_name="get_hostname",
            arguments={},
        )

        self.assertEqual(result.status, "denied")
        self.assertIsNotNone(result.run_id)

    def test_external_executable_is_not_registered(self):
        self.assertNotIn("run_registered_executable", self.registry.names())
        self.assertEqual(len(self.registry.names()), 53)

    async def test_list_directory_returns_counts_for_selected_depth(self):
        root = Path(__file__).resolve().parent
        expected_directories = sum(path.is_dir() for path in root.iterdir())
        expected_files = sum(path.is_file() for path in root.iterdir())

        result = await ListDirectoryTool().execute(
            ToolContext(
                user_id=1,
                conversation_id=None,
                allowed_roots=(root,),
            ),
            ListDirectoryArguments(path=str(root), max_depth=0),
        )

        self.assertEqual(result["directory_count"], expected_directories)
        self.assertEqual(result["file_count"], expected_files)
        self.assertEqual(result["max_depth"], 0)
        self.assertFalse(result["truncated"])

    def test_catalog_only_returns_system_and_current_users_tools(self):
        own_tool_id = self.create_user_tool(self.user_id, "own_test_tool")
        other_tool_id = self.create_user_tool(
            self.other_user_id,
            "other_test_tool",
        )

        first_page = self.repository.list_tools_page(self.user_id, 1, 50)
        second_page = self.repository.list_tools_page(self.user_id, 2, 50)
        items = first_page["items"] + second_page["items"]
        names = {item["tools_name"] for item in items}

        self.assertIn("get_current_time", names)
        self.assertIn("own_test_tool", names)
        self.assertNotIn("other_test_tool", names)
        own_tool = next(
            item for item in items if item["id"] == own_tool_id
        )
        self.assertTrue(own_tool["can_delete"])
        self.assertNotIn("source_kind", own_tool)
        with self.assertRaises(ToolNotFoundError):
            self.repository.get_tool_detail(self.user_id, other_tool_id)

    def test_user_can_disable_and_soft_delete_only_owned_tool(self):
        own_tool_id = self.create_user_tool(self.user_id, "managed_test_tool")
        other_tool_id = self.create_user_tool(
            self.other_user_id,
            "foreign_test_tool",
        )
        system_tool_id = self.db_manager.connection.execute(
            "SELECT id FROM agent_tools WHERE tools_name = 'get_current_time'"
        ).fetchone()["id"]

        updated = self.repository.set_user_tool_enabled(
            self.user_id,
            own_tool_id,
            False,
        )
        self.assertFalse(updated["is_enabled"])
        with self.assertRaises(ToolPermissionError):
            self.repository.set_user_tool_enabled(
                self.user_id,
                system_tool_id,
                False,
            )
        with self.assertRaises(ToolNotFoundError):
            self.repository.delete_user_tool(self.user_id, other_tool_id)

        deleted = self.repository.delete_user_tool(self.user_id, own_tool_id)
        self.assertEqual(deleted["id"], own_tool_id)
        deleted_row = self.db_manager.connection.execute(
            "SELECT deleted_at, is_enabled FROM agent_tools WHERE id = ?",
            (own_tool_id,),
        ).fetchone()
        self.assertIsNotNone(deleted_row["deleted_at"])
        self.assertEqual(deleted_row["is_enabled"], 0)
        with self.assertRaises(ToolNotFoundError):
            self.repository.get_tool_detail(self.user_id, own_tool_id)
