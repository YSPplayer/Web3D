# import os
## 告诉litellm从本地读取配置，不从github拉取
# os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
# os.environ["LITELLM_LOG"] = "ERROR"
import sys
import json
import asyncio
import litellm
async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raw = sys.stdin.read()
    payload = json.loads(raw)
    model = payload["model"]
    api_key = payload["api_key"]
    messages = payload["messages"]
    temperature = payload["temperature"]
    response = None
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            api_key=api_key,
            stream=True
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
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
                    "type": "done"
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
