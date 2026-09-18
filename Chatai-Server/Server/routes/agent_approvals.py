from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from Agent.approval_manager import (
    ApprovalNotFoundError,
    ApprovalPermissionError,
)


class AgentApprovalDecisionRequest(BaseModel):
    approved: bool


def create_agent_approvals_router(
    approval_manager,
    current_user_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(
        prefix="/chatai/agent/approvals",
        tags=["Agent Approvals"],
    )

    @router.post("/{approval_id}/decision")
    async def decide_agent_tool_approval(
        approval_id: str,
        decision: AgentApprovalDecisionRequest,
        current_user: dict = Depends(current_user_dependency),
    ):
        try:
            status = await approval_manager.decide(
                approval_id,
                current_user["id"],
                decision.approved,
            )
        except ApprovalPermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ApprovalNotFoundError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "code": 200,
            "message": "高风险工具审批已处理",
            "data": {
                "approval_id": approval_id,
                "status": status,
            },
        }

    return router
