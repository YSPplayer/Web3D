import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from Model.modelapi import ModelApi


class FakeStreamResponse:
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for chunk in self.chunks:
            yield chunk

    async def aclose(self):
        self.closed = True


def make_chunk(content: str | None, finish_reason: str | None = None):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            delta=SimpleNamespace(content=content),
            finish_reason=finish_reason,
        )]
    )


def make_completion(
    content: str | None,
    finish_reason: str = "stop",
    reasoning_content: str | None = None,
):
    return SimpleNamespace(
        id="response-1",
        choices=[SimpleNamespace(
            message=SimpleNamespace(
                content=content,
                reasoning_content=reasoning_content,
            ),
            finish_reason=finish_reason,
        )],
    )


class ModelApiStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_online_stream_exposes_provider_finish_reason(self):
        response = FakeStreamResponse([
            make_chunk("hello"),
            make_chunk(None, "length"),
        ])
        finish_state = {}
        contents = []

        with patch(
            "Model.modelapi.litellm.acompletion",
            new=AsyncMock(return_value=response),
        ):
            async for content in ModelApi().chat_stream(
                "provider/model",
                "secret",
                [{"role": "user", "content": "test"}],
                finish_state=finish_state,
            ):
                contents.append(content)

        self.assertEqual(contents, ["hello"])
        self.assertEqual(finish_state["reason"], "length")
        self.assertTrue(response.closed)

    async def test_non_stream_completion_collects_diagnostics(self):
        completion = make_completion("{\"type\":\"final\"}")
        finish_state = {}

        with patch(
            "Model.modelapi.litellm.acompletion",
            new=AsyncMock(return_value=completion),
        ) as mocked_completion, patch.object(
            ModelApi,
            "_supports_json_response",
            return_value=False,
        ):
            content = await ModelApi().chat_complete(
                "provider/model",
                "secret",
                [{"role": "user", "content": "test"}],
                json_mode=True,
                finish_state=finish_state,
            )

        self.assertEqual(content, '{"type":"final"}')
        request_data = mocked_completion.await_args.kwargs
        self.assertFalse(request_data["stream"])
        self.assertNotIn("response_format", request_data)
        self.assertEqual(finish_state["response_id"], "response-1")
        self.assertEqual(finish_state["content_chars"], len(content))
        self.assertFalse(finish_state["structured_json"])

    async def test_non_stream_completion_enables_supported_json_mode(self):
        completion = make_completion("", reasoning_content="internal")
        finish_state = {}

        with patch(
            "Model.modelapi.litellm.acompletion",
            new=AsyncMock(return_value=completion),
        ) as mocked_completion, patch.object(
            ModelApi,
            "_supports_json_response",
            return_value=True,
        ):
            content = await ModelApi().chat_complete(
                "provider/model",
                "secret",
                [{"role": "user", "content": "test"}],
                json_mode=True,
                finish_state=finish_state,
            )

        self.assertEqual(content, "")
        self.assertEqual(
            mocked_completion.await_args.kwargs["response_format"],
            {"type": "json_object"},
        )
        self.assertEqual(finish_state["reasoning_chars"], 8)
        self.assertTrue(finish_state["structured_json"])


if __name__ == "__main__":
    unittest.main()
