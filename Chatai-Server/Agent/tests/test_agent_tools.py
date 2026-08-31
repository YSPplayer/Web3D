import sqlite3
import threading
import unittest
from pathlib import Path

from Agent.factory import build_default_registry
from Agent.tool_dispatcher import ToolDispatcher
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

    async def test_registered_python_tool_can_run_after_binding(self):
        self.repository.set_user_tool_binding(1, "get_current_time", True)
        dispatcher = ToolDispatcher(self.registry, self.repository)

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

    async def test_unbound_tool_is_denied_and_audited(self):
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
