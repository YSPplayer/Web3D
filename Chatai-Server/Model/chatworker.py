# import os
## 告诉litellm从本地读取配置，不从github拉取
# os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
# os.environ["LITELLM_LOG"] = "ERROR"
import sys
import json
import asyncio
import litellm


def content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return "" if content is None else str(content)

    parts = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
            continue
        if isinstance(item, dict):
            text = item.get("text") or item.get("content")
        else:
            text = getattr(item, "text", None)
        if text:
            parts.append(str(text))
    return "".join(parts)


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raw = sys.stdin.read()
    payload = json.loads(raw)
    model = payload["model"]
    api_key = payload["api_key"]
    messages = payload["messages"]
    temperature = payload["temperature"]
    max_output_tokens = payload.get(
        "max_output_tokens",
        payload.get("max_tokens"),
    )
    stream = bool(payload.get("stream", True))
    response_format = payload.get("response_format")
    response = None
    try:
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "api_key": api_key,
            "stream": stream,
        }
        if max_output_tokens is not None:
            request_data["max_tokens"] = max_output_tokens
        if response_format:
            request_data["response_format"] = response_format
        response = await litellm.acompletion(**request_data)

        if not stream:
            choice = response.choices[0]
            response_message = choice.message
            content = content_to_text(
                getattr(response_message, "content", None)
            )
            reasoning_content = content_to_text(
                getattr(response_message, "reasoning_content", None)
            )
            print(
                json.dumps(
                    {
                        "type": "complete",
                        "content": content,
                        "finish_reason": str(
                            getattr(choice, "finish_reason", None) or "stop"
                        ),
                        "response_id": getattr(response, "id", None),
                        "reasoning_chars": len(reasoning_content),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            return

        finish_reason = None
        async for chunk in response:
            choice = chunk.choices[0]
            choice_finish_reason = getattr(choice, "finish_reason", None)
            if choice_finish_reason:
                finish_reason = str(choice_finish_reason)
            content = choice.delta.content
            if content:
                print(
                    json.dumps(
                        {
                            "type": "delta",
                            "content": content
                        },
                        ensure_ascii=False
                    ),
                    flush=True
                )
        print(
            json.dumps(
                {
                    "type": "done",
                    "finish_reason": finish_reason or "stop"
                },
                ensure_ascii=False
            ),
            flush=True
        )
    except Exception as exc:
        print(f"子进程模型调用失败: {exc}", file=sys.stderr, flush=True)

        print(
            json.dumps(
                {
                    "type": "error",
                    "message": str(exc)
                },
                ensure_ascii=False
            ),
            flush=True
        )

        sys.exit(1)

    finally:
        close = getattr(response, "aclose", None)
        if close:
            await close()


if __name__ == "__main__":
    asyncio.run(main())
