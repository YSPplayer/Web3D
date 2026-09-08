import asyncio
from dataclasses import dataclass
from uuid import uuid4

from Agent.context import ToolPolicy
from System.log_manager import get_logger


logger = get_logger(__name__)


class ApprovalNotFoundError(LookupError):
    pass


class ApprovalPermissionError(PermissionError):
    pass


@dataclass(slots=True)
class PendingToolApproval:
    approval_id: str
    request_id: str
    user_id: int
    conversation_id: int
    message_id: int | None
    policy: ToolPolicy
    arguments: dict
    future: asyncio.Future[str]


class AgentApprovalManager:
    """管理单进程内等待中的工具审批，并同步写入审计记录。"""

    def __init__(self, repository, *, timeout_seconds: int = 120):
        self.repository = repository
        self.timeout_seconds = max(1, timeout_seconds)
        self._pending: dict[str, PendingToolApproval] = {}
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        await asyncio.to_thread(self.repository.cancel_stale_pending)

    async def create(
        self,
        *,
        request_id: str,
        user_id: int,
        conversation_id: int,
        message_id: int | None,
        policy: ToolPolicy,
        arguments: dict,
    ) -> PendingToolApproval:
        approval_id = uuid4().hex
        future = asyncio.get_running_loop().create_future()
        approval = PendingToolApproval(
            approval_id=approval_id,
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            policy=policy,
            arguments=dict(arguments),
            future=future,
        )
        await asyncio.to_thread(
            self.repository.create,
            approval_id=approval_id,
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            tool_id=policy.tool_id,
            tools_name=policy.tool_name,
            display_name=policy.display_name,
            description=policy.description,
            arguments=approval.arguments,
        )
        async with self._lock:
            self._pending[approval_id] = approval
        logger.info(
            "等待高风险工具审批，approval_id=%s user_id=%s tool=%s",
            approval_id,
            user_id,
            policy.tool_name,
        )
        return approval

    async def wait(self, approval_id: str) -> str:
        async with self._lock:
            approval = self._pending.get(approval_id)
        if approval is None:
            raise ApprovalNotFoundError("工具审批请求不存在或已经结束")

        try:
            return await asyncio.wait_for(
                asyncio.shield(approval.future),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self._finish_pending(
                approval,
                status="expired",
                reason="approval_timeout",
                outcome="expired",
            )
            return "expired"
        except asyncio.CancelledError:
            await self._finish_pending(
                approval,
                status="cancelled",
                reason="generation_cancelled",
                outcome="cancelled",
            )
            raise
        finally:
            async with self._lock:
                if self._pending.get(approval_id) is approval:
                    self._pending.pop(approval_id, None)

    async def decide(
        self,
        approval_id: str,
        user_id: int,
        approved: bool,
    ) -> str:
        async with self._lock:
            approval = self._pending.get(approval_id)
            if approval is None:
                raise ApprovalNotFoundError("工具审批请求不存在或已经结束")
            if approval.user_id != user_id:
                raise ApprovalPermissionError("无权处理其他用户的工具审批")
            if approval.future.done():
                raise ApprovalNotFoundError("工具审批请求已经结束")
            status = "approved" if approved else "rejected"
            reason = "user_approved" if approved else "user_rejected"
            updated = await asyncio.to_thread(
                self.repository.resolve,
                approval_id,
                status,
                reason,
            )
            if not updated:
                raise ApprovalNotFoundError("工具审批请求已经结束")
            approval.future.set_result(status)

        logger.info(
            "高风险工具审批完成，approval_id=%s user_id=%s tool=%s status=%s",
            approval_id,
            user_id,
            approval.policy.tool_name,
            status,
        )
        return status

    async def cancel_all(self) -> None:
        async with self._lock:
            approvals = list(self._pending.values())
        for approval in approvals:
            await self._finish_pending(
                approval,
                status="cancelled",
                reason="server_shutdown",
                outcome="cancelled",
            )

    async def _finish_pending(
        self,
        approval: PendingToolApproval,
        *,
        status: str,
        reason: str,
        outcome: str,
    ) -> None:
        async with self._lock:
            if self._pending.get(approval.approval_id) is not approval:
                return
            await asyncio.to_thread(
                self.repository.resolve,
                approval.approval_id,
                status,
                reason,
            )
            self._pending.pop(approval.approval_id, None)
            if not approval.future.done():
                approval.future.set_result(outcome)
