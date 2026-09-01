import sqlite3
import threading
import unittest
from pathlib import Path

from Agent.context import ToolContext
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
        self.db_manager.connection.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            ("agent_test", "test_hash"),
        )
        self.db_manager.connection.commit()

        self.registry = build_default_registry()
        self.repository = AgentToolRepository(self.db_manager)
        self.repository.sync_definitions(self.registry.definitions())

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
        )

        self.assertEqual(result.status, "success")
        self.assertIn("datetime", result.data)
        run = self.db_manager.connection.execute(
            "SELECT status FROM agent_tool_runs WHERE id = ?",
            (result.run_id,),
        ).fetchone()
        self.assertEqual(run["status"], "success")

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
        self.assertEqual(len(self.registry.names()), 19)

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
