import asyncio
import shutil
import sqlite3
import threading
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Agent.factory import build_default_registry
from Agent.tool_dispatcher import ToolDispatcher
from Agent.user_tools import (
    UserToolProcessExecutor,
    UserToolStorage,
    UserToolUploadService,
)
from Data.agent_tool_repository import AgentToolRepository
from Server.routes.agent_tools import create_agent_tools_router


VALID_SOURCE = """from pydantic import BaseModel
from Agent.base import PythonTool
from Agent.context import ToolContext

class Arguments(BaseModel):
    value: str

class Tool(PythonTool[Arguments]):
    name = "route_upload_tool"
    display_name = "路由上传工具"
    description = "验证 multipart 上传接口"
    args_model = Arguments
    platform = "all"

    async def execute(self, context: ToolContext, arguments: Arguments) -> dict:
        return {"value": arguments.value}

tool = Tool()
"""


class MemoryDbManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.connection = sqlite3.connect(":memory:", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        sql_path = Path(__file__).resolve().parents[2] / "Sql" / "run.sql"
        self.connection.executescript(sql_path.read_text(encoding="utf-8"))
        self.connection.execute(
            "INSERT INTO users(username, password_hash) VALUES ('route', 'hash')"
        )
        self.connection.commit()

    def get_db_connection(self):
        return self.connection

    @staticmethod
    def now_time():
        return "2026-09-03 12:00:00"

    def close(self):
        self.connection.close()


class AgentToolUploadRouteTests(unittest.TestCase):
    def setUp(self):
        self.db_manager = MemoryDbManager()
        self.repository = AgentToolRepository(self.db_manager)
        self.storage_root = Path(__file__).resolve().parent / ".upload_route_storage"
        shutil.rmtree(self.storage_root, ignore_errors=True)
        process_executor = UserToolProcessExecutor(self.storage_root)
        self.dispatcher = ToolDispatcher(
            build_default_registry(),
            self.repository,
            process_executor,
        )
        upload_service = UserToolUploadService(
            self.repository,
            UserToolStorage(self.storage_root),
            process_executor,
        )

        async def current_user():
            return {"id": 1, "session_id": "route-test"}

        test_app = FastAPI()
        test_app.include_router(
            create_agent_tools_router(
                self.dispatcher,
                current_user,
                upload_service,
            )
        )
        self.client = TestClient(test_app)

    def tearDown(self):
        self.client.close()
        self.db_manager.close()
        shutil.rmtree(self.storage_root, ignore_errors=True)

    @staticmethod
    def form_data() -> dict:
        return {
            "tools_name": "route_upload_tool",
            "display_name": "路由上传工具",
            "description": "验证 multipart 上传接口",
            "platform": "all",
        }

    def test_upload_route_can_enable_and_execute_valid_user_tool(self):
        response = self.client.post(
            "/chatai/agent/tools",
            data=self.form_data(),
            files={"file": ("tool.py", VALID_SOURCE, "text/x-python")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["tools_name"], "route_upload_tool")
        self.assertFalse(data["is_enabled"])
        enable_response = self.client.patch(
            f"/chatai/agent/tools/{data['id']}/state",
            json={"is_enabled": True},
        )
        self.assertEqual(enable_response.status_code, 200, enable_response.text)
        self.assertTrue(enable_response.json()["data"]["is_enabled"])

        schemas = asyncio.run(self.dispatcher.model_schemas_for_user(1))
        schema = next(
            item
            for item in schemas
            if item["function"]["name"] == "route_upload_tool"
        )
        self.assertIn("value", schema["function"]["parameters"]["properties"])

        result = asyncio.run(
            self.dispatcher.execute(
                user_id=1,
                conversation_id=None,
                tool_name="route_upload_tool",
                arguments={"value": "hello"},
            )
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.data, {"value": "hello"})

    def test_upload_route_returns_structured_validation_errors(self):
        response = self.client.post(
            "/chatai/agent/tools",
            data=self.form_data(),
            files={"file": ("tool.txt", "not python", "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertEqual(detail["message"], "Agent 工具校验失败")
        self.assertTrue(detail["errors"])

    def test_example_route_returns_canonical_tool_source(self):
        response = self.client.get("/chatai/agent/tools/example")

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(data["filename"], "count_directories.py")
        self.assertIn("class CountDirectoriesTool", data["source"])


if __name__ == "__main__":
    unittest.main()
