#pip install litellm -i https://pypi.tuna.tsinghua.edu.cn/simple
import litellm
import asyncio
import json
import os
import sys
from pathlib import Path
from System.log_manager import get_logger


logger = get_logger(__name__)
class ModelApi:
    @staticmethod
    def _content_to_text(content) -> str:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return "" if content is None else str(content)

        parts: list[str] = []
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

    @staticmethod
    def _supports_json_response(model: str) -> bool:
        try:
            return bool(litellm.supports_response_schema(model=model))
        except Exception as exc:
            logger.debug(
                "无法判断模型是否支持 JSON 响应，model=%s error=%s",
                model,
                exc,
            )
            return False

    def get_token_count(
        self,
        model: str,
        text: str | None = None,
        messages: list[dict] | None = None,
    ):
        return litellm.token_counter(
            model=model,
            text=text,
            messages=messages,
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
        content = response.choices[0].message.content or ""
        logger.debug("模型同步调用完成，response_chars=%s", len(content))

    async def collect_stderr(self, stream):
        errors = []
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                errors.append(text)
                logger.warning("模型子进程 stderr：%s", text)

        return errors
    
    async def chat_stream(self, model: str, api_key: str, message: list[dict], proxy_host: str | None = None,
        proxy_port: int | None = None,
        proxy_active: int = 0,
        temperature: float = 0.6,
        max_output_tokens: int | None = None,
        finish_state: dict | None = None):
        response = None
        use_proxy = (
            int(proxy_active or 0) == 1
            and proxy_host
            and proxy_port
        )
        if not use_proxy:#非代理下直接返回
            try:
                request_data = {
                    "model": model,
                    "messages": message,
                    "temperature": temperature,
                    "api_key": api_key,
                    "stream": True,
                }
                if max_output_tokens is not None:
                    request_data["max_tokens"] = max_output_tokens
                response = await litellm.acompletion(
                    **request_data
                )
                chunk_count = 0
                content_chunk_count = 0
                async for chunk in response:
                    chunk_count += 1
                    choice = chunk.choices[0]
                    finish_reason = getattr(choice, "finish_reason", None)
                    if finish_reason and finish_state is not None:
                        finish_state["reason"] = str(finish_reason)
                    if finish_state is not None:
                        finish_state["response_id"] = getattr(
                            chunk,
                            "id",
                            finish_state.get("response_id"),
                        )
                    content = self._content_to_text(
                        getattr(choice.delta, "content", None)
                    )
                    if content:
                        content_chunk_count += 1
                        yield content
                if finish_state is not None:
                    finish_state["chunk_count"] = chunk_count
                    finish_state["content_chunk_count"] = content_chunk_count
            except asyncio.CancelledError:
                logger.info("模型流式生成已取消")
                raise
            finally:
                close = getattr(response, "aclose", None)
                if close:
                    await close()
            return
        #代理模式下启动新进程调用
        worker_path = Path(__file__).resolve().parent / "chatworker.py"
        server_root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proxy_url = self.build_proxy_url(proxy_host, proxy_port)
        logger.info("模型代理已启用，proxy=%s", proxy_url)
        env["HTTP_PROXY"] = proxy_url
        env["HTTPS_PROXY"] = proxy_url
        env["ALL_PROXY"] = proxy_url
        payload = {
            "model": model,
            "api_key": api_key,
            "messages": message,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
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
                if not text.startswith("{"):
                    logger.warning("模型子进程非 JSON 输出：%s", text[:2000])
                    continue
                event = json.loads(text)

                if event["type"] == "delta":
                    yield event["content"]
                elif event["type"] == "done":
                    if finish_state is not None:
                        finish_state["reason"] = event.get(
                            "finish_reason",
                            "stop",
                        )
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
            logger.info("代理模型流式生成已取消")
            raise

        finally:
            if stderr_task and not stderr_task.done():
                stderr_task.cancel()

    async def chat_complete(
        self,
        model: str,
        api_key: str,
        messages: list[dict],
        proxy_host: str | None = None,
        proxy_port: int | None = None,
        proxy_active: int = 0,
        temperature: float = 0,
        max_output_tokens: int | None = None,
        json_mode: bool = False,
        finish_state: dict | None = None,
    ) -> str:
        """执行不需要流式展示的短响应调用，例如 Agent JSON 决策。"""
        use_proxy = (
            int(proxy_active or 0) == 1
            and proxy_host
            and proxy_port
        )
        structured_json = (
            json_mode and self._supports_json_response(model)
        )
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "api_key": api_key,
            "stream": False,
        }
        if max_output_tokens is not None:
            request_data["max_tokens"] = max_output_tokens
        if structured_json:
            request_data["response_format"] = {"type": "json_object"}

        if use_proxy:
            return await self._chat_complete_with_proxy(
                request_data,
                str(proxy_host),
                int(proxy_port),
                finish_state,
                structured_json,
            )

        response = await litellm.acompletion(**request_data)
        choice = response.choices[0]
        response_message = choice.message
        content = self._content_to_text(
            getattr(response_message, "content", None)
        )
        reasoning_content = self._content_to_text(
            getattr(response_message, "reasoning_content", None)
        )
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_state is not None:
            finish_state.update({
                "reason": str(finish_reason or "stop"),
                "response_id": getattr(response, "id", None),
                "content_chars": len(content),
                "reasoning_chars": len(reasoning_content),
                "structured_json": structured_json,
            })
        logger.debug(
            "模型非流式调用完成，model=%s response_id=%s "
            "finish_reason=%s content_chars=%s reasoning_chars=%s "
            "structured_json=%s",
            model,
            getattr(response, "id", None),
            finish_reason,
            len(content),
            len(reasoning_content),
            structured_json,
        )
        return content

    async def _chat_complete_with_proxy(
        self,
        request_data: dict,
        proxy_host: str,
        proxy_port: int,
        finish_state: dict | None,
        structured_json: bool,
    ) -> str:
        worker_path = Path(__file__).resolve().parent / "chatworker.py"
        server_root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proxy_url = self.build_proxy_url(proxy_host, proxy_port)
        logger.info("模型代理已启用，proxy=%s", proxy_url)
        env["HTTP_PROXY"] = proxy_url
        env["HTTPS_PROXY"] = proxy_url
        env["ALL_PROXY"] = proxy_url
        payload = {
            **request_data,
            "response_format": request_data.get("response_format"),
        }
        process = None
        stderr_task = None
        result_content: str | None = None
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                str(worker_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(server_root),
            )
            process.stdin.write(
                json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
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
                if not text.startswith("{"):
                    logger.warning("模型子进程非 JSON 输出：%s", text[:2000])
                    continue
                event = json.loads(text)
                if event.get("type") == "complete":
                    result_content = self._content_to_text(
                        event.get("content")
                    )
                    if finish_state is not None:
                        finish_state.update({
                            "reason": event.get("finish_reason", "stop"),
                            "response_id": event.get("response_id"),
                            "content_chars": len(result_content),
                            "reasoning_chars": int(
                                event.get("reasoning_chars", 0)
                            ),
                            "structured_json": structured_json,
                        })
                elif event.get("type") == "error":
                    raise RuntimeError(event.get("message", "模型调用失败"))

            return_code = await process.wait()
            stderr_errors = await stderr_task if stderr_task else []
            if return_code != 0:
                raise RuntimeError(
                    "\n".join(stderr_errors)
                    or f"子进程退出异常: {return_code}"
                )
            if result_content is None:
                raise RuntimeError("模型子进程未返回 complete 事件")
            return result_content
        except asyncio.CancelledError:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            logger.info("代理模型非流式生成已取消")
            raise
        finally:
            if stderr_task and not stderr_task.done():
                stderr_task.cancel()
modelApi = ModelApi()
