import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Agent.approval_manager import ApprovalNotFoundError
from Server.routes.agent_approvals import create_agent_approvals_router


class FakeApprovalManager:
    def __init__(self):
        self.calls: list[tuple[str, int, bool]] = []

    async def decide(self, approval_id: str, user_id: int, approved: bool) -> str:
        self.calls.append((approval_id, user_id, approved))
        if approval_id == "expired":
            raise ApprovalNotFoundError("工具审批请求已经结束")
        return "approved" if approved else "rejected"


class AgentApprovalRouteTests(unittest.TestCase):
    def setUp(self):
        self.manager = FakeApprovalManager()
        app = FastAPI()
        app.include_router(
            create_agent_approvals_router(
                self.manager,
                lambda: {"id": 3},
            )
        )
        self.client = TestClient(app)

    def test_decision_uses_authenticated_user(self):
        response = self.client.post(
            "/chatai/agent/approvals/approval-1/decision",
            json={"approved": True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.manager.calls, [("approval-1", 3, True)])
        self.assertEqual(response.json()["data"]["status"], "approved")

    def test_finished_approval_cannot_be_decided_again(self):
        response = self.client.post(
            "/chatai/agent/approvals/expired/decision",
            json={"approved": False},
        )

        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
