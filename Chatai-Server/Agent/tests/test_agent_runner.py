import json
import unittest
from types import SimpleNamespace

from Agent.result import ToolExecutionResult
from Agent.runner import AgentRunner


class FakeDispatcher:
    def __init__(
        self,
        result_status: str = "success",
        *,
        requires_confirmation: bool = False,
        risk_level: str = "low",
    ):
        self.result_status = result_status
        self.requires_confirmation = requires_confirmation
        self.risk_level = risk_level
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
            {
                "type": "function",
                "function": {
                    "name": "delete_path",
                    "description": "删除单个文件或目录，目录可递归删除",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "path": {"type": "string"},
                            "recursive": {"type": "boolean"},
                            "use_trash": {"type": "boolean"},
                        },
                        "required": ["path"],
                    },
                },
            },
        ]

    async def execute(self, **kwargs) -> ToolExecutionResult:
        self.calls.append(kwargs)
        if kwargs["tool_name"] == "list_directory":
            data = {
                "path": kwargs["arguments"]["path"],
                "entries": [
                    {
                        "name": "folder-a",
                        "relative_path": "folder-a",
                        "type": "directory",
                    },
                    {
                        "name": "file.txt",
                        "relative_path": "file.txt",
                        "type": "file",
                    },
                ],
                "file_count": 1,
                "directory_count": 1,
                "max_depth": kwargs["arguments"].get("max_depth", 0),
                "truncated": False,
            }
        elif kwargs["tool_name"] == "delete_path":
            data = {
                "path": kwargs["arguments"]["path"],
                "deleted": True,
                "mode": "trash",
            }
        else:
            data = {"datetime": "2026-08-31 12:00:00"}
        return ToolExecutionResult(
            run_id=1,
            tool_name=kwargs["tool_name"],
            status=self.result_status,
            data=data if self.result_status == "success" else None,
            error=None if self.result_status == "success" else "工具不可用",
        )

    async def get_tool_policy(self, user_id: int, tool_name: str):
        return SimpleNamespace(
            tool_id=1,
            tool_name=tool_name,
            display_name="测试工具",
            description="测试工具描述",
            source_kind="system",
            is_enabled=True,
            requires_confirmation=self.requires_confirmation,
            risk_level=self.risk_level,
        )


class AgentRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_result_is_sent_back_before_final_answer(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        decisions = iter([
            '{"type":"tool","tool_name":"get_current_time","arguments":{}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
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

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
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

    async def test_missing_required_tool_argument_is_retried_before_execution(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher, max_decision_retries=1)
        decisions = iter([
            '{"type":"tool","tool_name":"list_directory","arguments":{}}',
            '{"type":"tool","tool_name":"list_directory",'
            '"arguments":{"path":"E:\\\\case_query\\\\data_out_x3p"}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            yield "目录查询完成"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=49,
                messages=[{
                    "role": "user",
                    "content": (
                        "E:\\case_query\\data_out_x3p 分析一下这里有多少文件"
                    ),
                }],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(len(dispatcher.calls), 1)
        self.assertEqual(
            dispatcher.calls[0]["arguments"]["path"],
            "E:\\case_query\\data_out_x3p",
        )
        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta"],
        )

    async def test_empty_decision_is_retried_without_empty_assistant_message(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher, max_decision_retries=1)
        decisions = iter([
            "",
            '{"type":"final","reason_code":"knowledge_only"}',
        ])
        decision_calls = []

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            decision_calls.append([dict(message) for message in messages])
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            yield "回答完成"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=49,
                messages=[{"role": "user", "content": "解释矩阵乘法"}],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual([event["type"] for event in events], ["delta"])
        self.assertEqual(len(decision_calls), 2)
        self.assertFalse(any(
            message.get("role") == "assistant"
            and not str(message.get("content", "")).strip()
            for message in decision_calls[1]
        ))
        self.assertIn("上一个模型响应为空", decision_calls[1][-1]["content"])

    async def test_repeated_tool_failure_returns_deterministic_error(self):
        dispatcher = FakeDispatcher(result_status="denied")
        runner = AgentRunner(dispatcher, max_failed_tools=1)

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return (
                '{"type":"tool","tool_name":"get_current_time",'
                '"arguments":{}}'
            )

        async def stream_model(messages: list[dict], metadata: dict):
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

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
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

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
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

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
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

    async def test_final_decision_ignores_harmless_data_field(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        decisions = iter([
            '{"type":"tool","tool_name":"get_current_time","arguments":{}}',
            '{"type":"final","reason_code":"completed_with_tool",'
            '"data":{"datetime":"2026-08-31 12:00:00"}}',
        ])

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            yield "当前时间是 2026-08-31 12:00:00"

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
            ["tool_start", "tool_result", "delta"],
        )
        self.assertEqual(len(dispatcher.calls), 1)

    async def test_successful_identical_tool_call_is_not_executed_twice(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        duplicate_decision = (
            '{"type":"tool","tool_name":"get_current_time",'
            '"arguments":{}}'
        )
        decisions = iter([duplicate_decision, duplicate_decision])

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            yield "目录查询完成"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=56,
                messages=[{
                    "role": "user",
                    "content": "查询当前系统时间",
                }],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta"],
        )
        self.assertEqual(len(dispatcher.calls), 1)

    async def test_natural_answer_after_successful_tool_becomes_implicit_final(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        decisions = iter([
            '{"type":"tool","tool_name":"get_current_time","arguments":{}}',
            "当前系统时间是 2026-08-31 12:00:00。",
        ])

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            yield "当前系统时间是 2026-08-31 12:00:00。"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=56,
                messages=[{"role": "user", "content": "查询当前系统时间"}],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "delta"],
        )
        self.assertEqual(len(dispatcher.calls), 1)

    async def test_direct_folder_request_forces_depth_zero_and_filters_files(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher)
        decisions = iter([
            '{"type":"tool","tool_name":"list_directory",'
            '"arguments":{"path":"D:\\\\MeasResults","max_depth":3}}',
        ])
        decision_calls = []

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            decision_calls.append(metadata)
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            serialized = json.dumps(messages, ensure_ascii=False)
            self.assertIn("folder-a", serialized)
            self.assertNotIn("file.txt", serialized)
            self.assertIn("direct_directories_only", serialized)
            yield "共有 1 个一级文件夹：folder-a"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=56,
                messages=[{
                    "role": "user",
                    "content": (
                        "帮我分析一下 D:\\MeasResults 这里的文件夹数量，"
                        "每一个文件夹的目录名也整理给我"
                    ),
                }],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertEqual(
            dispatcher.calls[0]["arguments"],
            {"path": "D:\\MeasResults", "max_depth": 0},
        )
        self.assertEqual(len(decision_calls), 1)
        self.assertEqual(decision_calls[0]["max_output_tokens"], 256)
        self.assertEqual(events[-1]["type"], "delta")

    async def test_delete_request_cannot_finish_after_read_only_preflight(self):
        dispatcher = FakeDispatcher()
        runner = AgentRunner(dispatcher, max_decision_retries=1)
        target = "E:\\case_query\\data_out_x3p\\92G_9800959_S1"
        decisions = iter([
            '{"type":"tool","tool_name":"list_directory",'
            '"arguments":{"path":"E:\\\\case_query\\\\data_out_x3p",'
            '"max_depth":0}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
            '{"type":"tool","tool_name":"delete_path",'
            '"arguments":{"path":"E:\\\\case_query\\\\data_out_x3p'
            '\\\\92G_9800959_S1","recursive":true,"use_trash":true}}',
            '{"type":"final","reason_code":"completed_with_tool"}',
        ])

        async def complete_model(messages: list[dict], metadata: dict) -> str:
            return next(decisions)

        async def stream_model(messages: list[dict], metadata: dict):
            self.assertTrue(any(
                '"deleted": true' in str(message.get("content", ""))
                for message in messages
            ))
            yield "目标文件夹已送入回收站"

        events = [
            event
            async for event in runner.run_stream(
                user_id=1,
                conversation_id=49,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "E:\\case_query\\data_out_x3p 中有文件夹 "
                            "92G_9800959_S1"
                        ),
                    },
                    {"role": "assistant", "content": "已经查询到该文件夹"},
                    {
                        "role": "user",
                        "content": (
                            "OK，帮我把这个92G_9800959_S1的文件夹和其内部的"
                            "文件全部删除，开始行动"
                        ),
                    },
                ],
                complete_model=complete_model,
                stream_model=stream_model,
            )
        ]

        self.assertTrue(AgentRunner._request_requires_tool([
            {
                "role": "user",
                "content": "把这个文件夹和其内部文件全部删除",
            }
        ]))
        self.assertEqual(
            [call["tool_name"] for call in dispatcher.calls],
            ["list_directory", "delete_path"],
        )
        self.assertEqual(dispatcher.calls[1]["arguments"]["path"], target)
        self.assertEqual(
            [event["type"] for event in events],
            ["tool_start", "tool_result", "tool_start", "tool_result", "delta"],
        )

    def test_delete_tool_is_pinned_into_limited_schema_selection(self):
        schemas = [
            {
                "type": "function",
                "function": {
                    "name": f"read_candidate_{index}",
                    "description": "读取文件和目录数据",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
            for index in range(15)
        ]
        schemas.append({
            "type": "function",
            "function": {
                "name": "delete_path",
                "description": "删除单个文件或目录",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        })

        selected = AgentRunner._select_tool_schemas(
            [{
                "role": "user",
                "content": "把这个文件夹及其内部文件全部删除",
            }],
            schemas,
            maximum=10,
        )

        selected_names = {
            schema["function"]["name"]
            for schema in selected
        }
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected_names, {"delete_path"})

    def test_decision_context_keeps_only_recent_messages_and_system(self):
        messages = [
            {"role": "system", "content": "system"},
            *[
                {"role": "user", "content": f"message-{index}"}
                for index in range(12)
            ],
        ]

        selected = AgentRunner._decision_context(messages)

        self.assertEqual(selected[0]["content"], "system")
        self.assertEqual(
            [message["content"] for message in selected[1:]],
            [f"message-{index}" for index in range(4, 12)],
        )


if __name__ == "__main__":
    unittest.main()
