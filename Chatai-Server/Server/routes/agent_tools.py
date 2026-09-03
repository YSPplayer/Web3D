from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from Agent.exceptions import (
    ToolNotFoundError,
    ToolPermissionError,
    ToolRepositoryError,
)
from System.log_manager import get_logger


logger = get_logger(__name__)


class AgentToolStateRequest(BaseModel):
    is_enabled: bool


def _success(message: str, data: Any = None) -> dict:
    return {
        "code": 200,
        "message": message,
        "data": data,
    }


def _raise_http_error(operation: str, exc: Exception) -> None:
    if isinstance(exc, ToolNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ToolPermissionError):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    logger.exception("Agent 工具%s失败", operation)
    raise HTTPException(
        status_code=500,
        detail=f"Agent 工具{operation}失败",
    ) from exc


def create_agent_tools_router(
    dispatcher,
    current_user_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(prefix="/chatai/agent/tools", tags=["Agent Tools"])

    @router.get("")
    async def list_agent_tools(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=6, ge=1, le=50),
        current_user: dict = Depends(current_user_dependency),
    ):
        try:
            result = await dispatcher.list_tools_page(
                current_user["id"],
                page,
                page_size,
            )
            return _success("Agent 工具查询成功", result)
        except ToolRepositoryError as exc:
            _raise_http_error("分页查询", exc)

    @router.get("/{tool_id}")
    async def get_agent_tool_detail(
        tool_id: int,
        current_user: dict = Depends(current_user_dependency),
    ):
        try:
            result = await dispatcher.get_tool_detail(
                current_user["id"],
                tool_id,
            )
            return _success("Agent 工具详情查询成功", result)
        except (ToolNotFoundError, ToolRepositoryError) as exc:
            _raise_http_error("详情查询", exc)

    @router.patch("/{tool_id}/state")
    async def update_agent_tool_state(
        tool_id: int,
        state: AgentToolStateRequest,
        current_user: dict = Depends(current_user_dependency),
    ):
        try:
            result = await dispatcher.set_user_tool_enabled(
                current_user["id"],
                tool_id,
                state.is_enabled,
            )
            return _success("Agent 工具状态更新成功", result)
        except (
            ToolNotFoundError,
            ToolPermissionError,
            ToolRepositoryError,
        ) as exc:
            _raise_http_error("状态更新", exc)

    @router.delete("/{tool_id}")
    async def delete_agent_tool(
        tool_id: int,
        current_user: dict = Depends(current_user_dependency),
    ):
        try:
            result = await dispatcher.delete_user_tool(
                current_user["id"],
                tool_id,
            )
            return _success(
                "Agent 工具删除成功",
                {
                    "id": result["id"],
                    "tools_name": result["tools_name"],
                },
            )
        except (
            ToolNotFoundError,
            ToolPermissionError,
            ToolRepositoryError,
        ) as exc:
            _raise_http_error("删除", exc)

    return router
