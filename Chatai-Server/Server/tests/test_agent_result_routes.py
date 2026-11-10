import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Agent.result_storage import create_name_comparison_result
from Config.config import config
from Server.routes.agent_results import create_agent_results_router


class AgentResultRoutesTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent
        )
        self.original_log_path = config.log_path
        config.log_path = Path(self.temporary_directory.name)
        app = FastAPI()
        app.include_router(create_agent_results_router(lambda: {"id": 7}))
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        config.log_path = self.original_log_path
        self.temporary_directory.cleanup()

    def test_user_can_download_own_generated_csv(self):
        path, url = create_name_comparison_result(7)
        path.write_text("name,path,type\nexample,x,file\n", encoding="utf-8")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("example", response.text)
        self.assertIn("attachment", response.headers["content-disposition"])

    def test_user_cannot_download_another_users_result(self):
        path, url = create_name_comparison_result(8)
        path.write_text("private", encoding="utf-8")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
