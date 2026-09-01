import unittest

from Agent.result import ToolExecutionResult
from Agent.runner import AgentRunner


class FakeDispatcher:
    def __init__(self, result_status: str = "success"):
        self.result_status = result_status
        self.calls: list[dict] = []

    async def model_schemas_for_user(self, user_id: int) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "获取当前时间",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出目录中的文件和子目录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "max_depth": {"type": "integer"},
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_stat",
                    "description": "查看文件或目录信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                        "required": ["path"],
                    },
                },
            },
        ]

    async def execute(self, **kwargs) -> ToolExecutionResult:
        self.calls.append(kwargs)
        return ToolExecutionResult(
            run_id=1,
            tool_name=kwargs["tool_name"],
            status=self.result_status,
            data={"datetime": "2026-08-31 12:00:00"}
            if self.result_status == "success"
            else None,
            error=None if self.result_status == "success" else "工具不可用",
        )


class AgentRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_result_is_sent_back_before_final_answer(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        decisions = iter([
            '{"type":"tool","tool_name":"get_current_time","arguments":{}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict]) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict]):
            self.assertIn("<tool_result>", str(messages))
            yield "当前时间是"
            yield "2026-08-31 12:00:00"

        events = [
            event
            async for event in runner.run_stream(
                user_id=3,
                conversation_id=25,
                messages=[{"role": "user", "content": "现在几点"}],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta", "delta"],
        )
        self.assertEqual(dispatcher.calls[0]["tool_name"], "get_current_time")
        self.assertEqual(dispatcher.calls[0]["arguments"], {})

    async def test_invalid_json_is_retried_without_executing_tool(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher, max_decision_retries=1)
        decisions = iter([
            "不是 JSON",
            '{"type":"final","reason_code":"knowledge_only"}',
        ])

        async def complete_model(messages: list[dict]) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict]):
            yield "当前不需要调用工具"

        events = [
            event
            async for event in runner.run_stream(
                user_id=3,
                conversation_id=25,
                messages=[{"role": "user", "content": "你好"}],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(events, [
            {"type": "delta", "content": "当前不需要调用工具"}
        ])
        self.assertEqual(dispatcher.calls, [])

    async def test_repeated_tool_failure_returns_deterministic_error(self):
        dispatcher = FakeDispatcher(result_status="denied")
        runner = AgentRunner(dispatcher, max_failed_tools=1)

        async def complete_model(messages: list[dict]) -> str:
            return (
                '{"type":"tool","tool_name":"get_current_time",'
                '"arguments":{}}'
            )

        async def stream_model(messages: list[dict]):
            self.fail("工具失败不应再次调用模型生成错误说明")
            yield ""

        events = [
            event
            async for event in runner.run_stream(
                user_id=3,
                conversation_id=25,
                messages=[{"role": "user", "content": "现在几点"}],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "agent_error"],
        )
        self.assertEqual(events[1]["status"], "denied")
        self.assertEqual(events[2]["code"], "tool_denied")

    async def test_external_request_rejects_early_final_and_calls_tool(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher, max_decision_retries=2)
        decisions = iter([
            '{"type":"final","reason_code":"knowledge_only"}',
            '{"type":"tool","tool_name":"list_directory",'
            '"arguments":{"path":"D:\\\\MeasResults","max_depth":0}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict]) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict]):
            yield "目录查询完成"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=56,
                messages=[{
                    "role": "user",
                    "content": "统计 D:\\MeasResults 的文件夹数量",
                }],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta"],
        )
        self.assertEqual(dispatcher.calls[0]["tool_name"], "list_directory")

    async def test_bare_tool_name_and_arguments_are_normalized(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        decisions = iter([
            'list_directory\n{"path":"D:\\\\MeasResults","max_depth":0}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict]) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict]):
            yield "目录中有 3 个文件夹"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=56,
                messages=[{
                    "role": "user",
                    "content": "统计 D:\\MeasResults 的文件夹数量",
                }],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta"],
        )
        self.assertEqual(dispatcher.calls[0]["tool_name"], "list_directory")
        self.assertEqual(
            dispatcher.calls[0]["arguments"],
            {"path": "D:\\MeasResults", "max_depth": 0},
        )

    async def test_existing_path_cannot_be_requested_again(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher, max_decision_retries=1)
        decisions = iter([
            '{"type":"clarification","missing_fields":["path"],'
            '"message":"需要用户补充的信息"}',
            '{"type":"tool","tool_name":"list_directory",'
            '"arguments":{"path":"D:\\\\MeasResults","max_depth":0}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict]) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict]):
            yield "目录查询完成"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=56,
                messages=[{
                    "role": "user",
                    "content": "帮我分析 D:\\MeasResults 文件夹数量",
                }],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta"],
        )
        self.assertEqual(dispatcher.calls[0]["tool_name"], "list_directory")


if __name__ == "__main__":
    unittest.main()
