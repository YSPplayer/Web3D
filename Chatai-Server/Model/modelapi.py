import litellm
import asyncio
import json
import os
import sys
from pathlib import Path
class ModelApi:
    def get_token_count(self,model:str,message: str):
        return litellm.token_counter(
        model=model,
        text=message
    )

    def build_proxy_url(self,ip: str, port: int) -> str:
        return f"http://{ip}:{port}"
    
    def build_messages(self,user_message:str,history_messages:dict):
        model_messages = []
        for item in history_messages:
            model_messages.append({
                "role": item["role"],
                "content": item["content"]
            })
        model_messages.append({
            "role": "user",
            "content": user_message
        })
        return model_messages

    def chat(self,model: str, api_key: str, message: str):
        response = litellm.completion(
            model = model,
            messages = [{"role": "user", "content": message}],
            temperature=0.6,
            api_key = api_key
        )
        print(response.choices[0].message.content)

    async def collect_stderr(self, stream):
        errors = []
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                errors.append(text)
                print(text)

        return errors
    
    async def chat_stream(self, model: str, api_key: str, message: list[dict], proxy_host: str | None = None,
        proxy_port: int | None = None,
        proxy_active: int = 0):
        response = None
        worker_path = Path(__file__).resolve().parent / "chatworker.py"
        server_root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        if proxy_active and proxy_host and proxy_port:
            proxy_url = self.build_proxy_url(proxy_host, proxy_port)
            print("代理已启用:" + proxy_url)
            env["HTTP_PROXY"] = proxy_url
            env["HTTPS_PROXY"] = proxy_url
            env["ALL_PROXY"] = proxy_url
        else:
            env.pop("HTTP_PROXY", None)
            env.pop("HTTPS_PROXY", None)
            env.pop("ALL_PROXY", None)
        payload = {
            "model": model,
            "api_key": api_key,
            "messages": message,
            "temperature": 0.6
        }
        process = None
        stderr_task = None
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                str(worker_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(server_root)
            )
            stdin_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            process.stdin.write(stdin_data)
            await process.stdin.drain()
            process.stdin.close()
            stderr_task = asyncio.create_task(
                self.collect_stderr(process.stderr)
            )
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                if not text:
                    continue
                event = json.loads(text)

                if event["type"] == "delta":
                    yield event["content"]
                elif event["type"] == "done":
                    break
                elif event["type"] == "error":
                    raise RuntimeError(event.get("message", "模型调用失败"))
            return_code = await process.wait()
            stderr_errors = []
            if stderr_task:
                stderr_errors = await stderr_task
            if return_code != 0:
                raise RuntimeError(
                    "\n".join(stderr_errors) or f"子进程退出异常: {return_code}"
                )
        except asyncio.CancelledError:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            print("模型流式生成已取消")
            raise

        finally:
            if stderr_task and not stderr_task.done():
                stderr_task.cancel()
modelApi = ModelApi()