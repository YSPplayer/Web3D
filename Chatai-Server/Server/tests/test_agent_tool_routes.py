import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from Data.db_manager import db_manager
from Server.server import app, get_current_user


class AgentToolRouteTests(unittest.TestCase):
    def setUp(self):
        self.original_db_path = db_manager.db_path
        db_manager.close_db()
        self.db_path = Path(__file__).resolve().parent / ".test_agent_routes.db"
        self.db_path.unlink(missing_ok=True)
        db_manager.db_path = self.db_path
        db_manager.init_db()

        connection = db_manager.get_db_connection()
        cursor = connection.execute(
            "INSERT INTO users(username, password_hash) VALUES ('owner', 'hash')"
        )
        self.user_id = cursor.lastrowid
        cursor = connection.execute(
            "INSERT INTO users(username, password_hash) VALUES ('other', 'hash')"
        )
        self.other_user_id = cursor.lastrowid
        self.own_tool_id = self._insert_user_tool("own_route_tool", self.user_id)
        self.other_tool_id = self._insert_user_tool(
            "other_route_tool",
            self.other_user_id,
        )
        self.system_tool_id = connection.execute(
            "SELECT id FROM agent_tools WHERE tools_name = 'get_current_time'"
        ).fetchone()["id"]
        connection.commit()

        async def current_test_user():
            return {"id": self.user_id, "session_id": "test-session"}

        app.dependency_overrides[get_current_user] = current_test_user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        db_manager.close_db()
        self.db_path.unlink(missing_ok=True)
        db_manager.db_path = self.original_db_path

    def _insert_user_tool(self, tool_name: str, owner_user_id: int) -> int:
        cursor = db_manager.get_db_connection().execute(
            """
            INSERT INTO agent_tools (
                tools_name,
                display_name,
                description,
                owner_user_id,
                source_kind,
                storage_path,
                entrypoint,
                code_sha256,
                validation_status
            ) VALUES (?, ?, 'route test', ?, 'user', ?, 'tool:Tool',
                      'sha256', 'valid')
            """,
            (
                tool_name,
                tool_name,
                owner_user_id,
                f"users/{owner_user_id}/{tool_name}/tool.py",
            ),
        )
        return cursor.lastrowid

    def test_routes_scope_tools_and_protect_system_rows(self):
        page = self.client.get(
            "/chatai/agent/tools",
            params={"page": 1, "page_size": 50},
        )
        self.assertEqual(page.status_code, 200)
        names = {
            item["tools_name"]
            for item in page.json()["data"]["items"]
        }
        self.assertIn("own_route_tool", names)
        self.assertNotIn("other_route_tool", names)

        own_detail = self.client.get(
            f"/chatai/agent/tools/{self.own_tool_id}"
        )
        self.assertEqual(own_detail.status_code, 200)
        foreign_detail = self.client.get(
            f"/chatai/agent/tools/{self.other_tool_id}"
        )
        self.assertEqual(foreign_detail.status_code, 404)

        system_update = self.client.patch(
            f"/chatai/agent/tools/{self.system_tool_id}/state",
            json={"is_enabled": False},
        )
        self.assertEqual(system_update.status_code, 403)
        own_update = self.client.patch(
            f"/chatai/agent/tools/{self.own_tool_id}/state",
            json={"is_enabled": False},
        )
        self.assertEqual(own_update.status_code, 200)
        self.assertFalse(own_update.json()["data"]["is_enabled"])

        deleted = self.client.delete(
            f"/chatai/agent/tools/{self.own_tool_id}"
        )
        self.assertEqual(deleted.status_code, 200)
        after_delete = self.client.get(
            f"/chatai/agent/tools/{self.own_tool_id}"
        )
        self.assertEqual(after_delete.status_code, 404)


if __name__ == "__main__":
    unittest.main()
