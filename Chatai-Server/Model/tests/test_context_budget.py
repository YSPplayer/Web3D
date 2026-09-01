import unittest

from Model.context_budget import ContextBudgetManager
from Model.token_manager import ModelTokenProfile


class FakeTokenCounter:
    async def count_messages(self, runtime: dict, messages: list[dict]) -> int:
        return sum(len(str(message.get("content", ""))) for message in messages)


class ContextBudgetManagerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = ContextBudgetManager(FakeTokenCounter())
        self.runtime = {"is_local_model": False, "model_name": "test/model"}

    async def test_chat_keeps_newest_complete_turns(self):
        history = [
            {"id": 1, "role": "user", "content": "old-user"},
            {"id": 2, "role": "assistant", "content": "old-answer"},
            {"id": 3, "role": "user", "content": "new-user"},
            {"id": 4, "role": "assistant", "content": "new-answer"},
        ]
        profile = ModelTokenProfile(
            context_window=37,
            max_output_tokens=5,
            safety_margin_tokens=5,
        )

        prepared = await self.manager.prepare_chat(
            self.runtime,
            profile,
            history,
            "current",
        )

        self.assertEqual(
            [message["content"] for message in prepared.messages],
            ["new-user", "new-answer", "current"],
        )
        self.assertEqual(prepared.truncated_messages, 2)
        self.assertEqual(
            [message["id"] for message in prepared.dropped_messages],
            [1, 2],
        )

    async def test_agent_keeps_system_current_user_and_latest_tool_result(self):
        messages = [
            {"role": "system", "content": "skill"},
            {"role": "user", "content": "old"},
            {"role": "assistant", "content": "old-answer"},
            {"role": "user", "content": "current-question"},
            {"role": "user", "content": "<tool_result>latest</tool_result>"},
            {"role": "user", "content": "请基于上面的真实对话和工具结果回答"},
        ]
        profile = ModelTokenProfile(
            context_window=100,
            max_output_tokens=10,
            safety_margin_tokens=5,
        )

        prepared = await self.manager.prepare_agent(
            self.runtime,
            profile,
            messages,
        )

        contents = [message["content"] for message in prepared.messages]
        self.assertIn("skill", contents)
        self.assertIn("current-question", contents)
        self.assertIn("<tool_result>latest</tool_result>", contents)
        self.assertIn("请基于上面的真实对话和工具结果回答", contents)


if __name__ == "__main__":
    unittest.main()
