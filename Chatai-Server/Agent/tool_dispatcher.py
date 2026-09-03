import asyncio
import json
import sys
from time import perf_counter
from pathlib import Path

from pydantic import ValidationError

from Agent.context import ToolContext, ToolPolicy
from Agent.exceptions import ToolNotFoundError
from Agent.result import ToolExecutionResult
from Agent.tool_registry import ToolRegistry
from System.log_manager import get_logger


logger = get_logger(__name__)


class ToolDispatcher:
    def __init__(self, registry: ToolRegistry, repository):
        self.registry = registry
        self.repository = repository

    async def sync_registered_tools(self) -> None:
        await asyncio.to_thread(
            self.repository.sync_definitions,
            self.registry.definitions(),
        )

    async def list_tools_page(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        return await asyncio.to_thread(
            self.repository.list_tools_page,
            user_id,
            page,
            page_size,
        )

    async def get_tool_detail(self, user_id: int, tool_id: int) -> dict:
        return await asyncio.to_thread(
            self.repository.get_tool_detail,
            user_id,
            tool_id,
        )

    async def set_user_tool_enabled(
        self,
        user_id: int,
        tool_id: int,
        is_enabled: bool,
    ) -> dict:
        return await asyncio.to_thread(
            self.repository.set_user_tool_enabled,
            user_id,
            tool_id,
            is_enabled,
        )

    async def delete_user_tool(self, user_id: int, tool_id: int) -> dict:
        return await asyncio.to_thread(
            self.repository.delete_user_tool,
            user_id,
            tool_id,
        )

    async def model_schemas_for_user(self, user_id: int) -> list[dict]:
        enabled_names = await asyncio.to_thread(
            self.repository.list_user_enabled_tool_names,
            user_id,
        )
        return self.registry.model_schemas(enabled_names)

    async def execute(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
        tool_name: str,
        arguments: dict,
        confirmation_granted: bool = False,
        step_index: int = 0,
        message_id: int | None = None,
    ) -> ToolExecutionResult:
        started_at = perf_counter()
        if not isinstance(arguments, dict):
            logger.warning(
                "工具参数类型错误，user_id=%s conversation_id=%s tool=%s",
                user_id,
                conversation_id,
                tool_name,
            )
            return ToolExecutionResult(
                run_id=None,
                tool_name=tool_name,
                status="failed",
                error="工具参数必须是 JSON 对象",
            )

        logger.info(
            "工具调度开始，user_id=%s conversation_id=%s tool=%s argument_keys=%s",
            user_id,
            conversation_id,
            tool_name,
            sorted(arguments.keys()),
        )

        policy = await asyncio.to_thread(
            self.repository.get_user_tool_policy,
            user_id,
            tool_name,
        )
        if policy is None:
            logger.warning("工具不存在，tool=%s", tool_name)
            return ToolExecutionResult(
                run_id=None,
                tool_name=tool_name,
                status="denied",
                error="工具不存在",
            )

        denied_reason = self._get_denied_reason(policy, confirmation_granted)
        if denied_reason:
            logger.warning(
                "工具执行被拒绝，user_id=%s conversation_id=%s tool=%s reason=%s",
                user_id,
                conversation_id,
                tool_name,
                denied_reason,
            )
            run_id = await asyncio.to_thread(
                self.repository.create_run,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id=policy.tool_id,
                tool_name=tool_name,
                arguments=arguments,
                status="denied",
                error_message=denied_reason,
                step_index=step_index,
                message_id=message_id,
            )
            return ToolExecutionResult(
                run_id=run_id,
                tool_name=tool_name,
                status="denied",
                error=denied_reason,
            )

        try:
            tool = self.registry.get(tool_name)
        except ToolNotFoundError as exc:
            logger.warning("Python 工具未注册，tool=%s error=%s", tool_name, exc)
            run_id = await asyncio.to_thread(
                self.repository.create_run,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id=policy.tool_id,
                tool_name=tool_name,
                arguments=arguments,
                status="denied",
                error_message=str(exc),
                step_index=step_index,
                message_id=message_id,
            )
            return ToolExecutionResult(
                run_id=run_id,
                tool_name=tool_name,
                status="denied",
                error=str(exc),
            )

        run_id = await asyncio.to_thread(
            self.repository.create_run,
            user_id=user_id,
            conversation_id=conversation_id,
            tool_id=policy.tool_id,
            tool_name=tool_name,
            arguments=arguments,
            status="running",
            step_index=step_index,
            message_id=message_id,
        )

        try:
            validated_arguments = tool.args_model.model_validate(arguments)
            context = ToolContext(
                user_id=user_id,
                conversation_id=conversation_id,
                allowed_roots=tuple(Path(root) for root in policy.allowed_roots),
            )
            data = await asyncio.wait_for(
                tool.execute(context, validated_arguments),
                timeout=policy.timeout_seconds,
            )
            limited_data = self._limit_output(data, policy.max_output_bytes)
            await asyncio.to_thread(
                self.repository.finish_run,
                run_id,
                status="success",
                result=limited_data,
            )
            logger.info(
                "工具执行成功，run_id=%s tool=%s elapsed_ms=%.2f",
                run_id,
                tool_name,
                (perf_counter() - started_at) * 1000,
            )
            return ToolExecutionResult(
                run_id=run_id,
                tool_name=tool_name,
                status="success",
                data=limited_data,
            )
        except ValidationError as exc:
            error = f"工具参数校验失败：{exc}"
            logger.warning(
                "工具参数校验失败，run_id=%s tool=%s error=%s",
                run_id,
                tool_name,
                exc,
            )
            await asyncio.to_thread(
                self.repository.finish_run,
                run_id,
                status="failed",
                error_message=error,
            )
            return ToolExecutionResult(run_id, tool_name, "failed", error=error)
        except asyncio.TimeoutError:
            error = f"工具执行超过 {policy.timeout_seconds} 秒"
            logger.warning(
                "工具执行超时，run_id=%s tool=%s timeout_seconds=%s",
                run_id,
                tool_name,
                policy.timeout_seconds,
            )
            await asyncio.to_thread(
                self.repository.finish_run,
                run_id,
                status="timeout",
                error_message=error,
            )
            return ToolExecutionResult(run_id, tool_name, "timeout", error=error)
        except asyncio.CancelledError:
            logger.info("工具执行已取消，run_id=%s tool=%s", run_id, tool_name)
            await asyncio.to_thread(
                self.repository.finish_run,
                run_id,
                status="failed",
                error_message="工具执行被取消",
            )
            raise
        except Exception as exc:
            error = str(exc)
            logger.exception("工具执行异常，run_id=%s tool=%s", run_id, tool_name)
            await asyncio.to_thread(
                self.repository.finish_run,
                run_id,
                status="failed",
                error_message=error,
            )
            return ToolExecutionResult(run_id, tool_name, "failed", error=error)

    @staticmethod
    def _current_platform() -> str:
        if sys.platform.startswith("win"):
            return "windows"
        if sys.platform.startswith("linux"):
            return "linux"
        return "all"

    def _get_denied_reason(
        self,
        policy: ToolPolicy,
        confirmation_granted: bool,
    ) -> str | None:
        if policy.tool_type != "python_builtin":
            return "当前调度器只允许执行已注册的 Python 工具"
        if not policy.is_enabled:
            return "工具已被系统禁用"
        current_platform = self._current_platform()
        if policy.platform not in {"all", current_platform}:
            return f"工具不支持当前平台：{current_platform}"
        if policy.requires_confirmation and not confirmation_granted:
            return "工具需要用户确认后才能执行"
        return None

    @staticmethod
    def _limit_output(data, max_output_bytes: int):
        encoded = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        if len(encoded) <= max_output_bytes:
            return data
        content = encoded[:max_output_bytes].decode("utf-8", errors="ignore")
        return {
            "truncated": True,
            "original_bytes": len(encoded),
            "content": content,
        }
