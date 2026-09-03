from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from Agent.examples import get_agent_tool_example
from Agent.exceptions import (
    ToolConflictError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRepositoryError,
    ToolRuntimeError,
    ToolStorageError,
    ToolValidationError,
)
from Agent.user_tools import UserToolUploadMetadata, UserToolUploadService
from Agent.user_tools.upload_service import MAX_TOOL_FILE_BYTES
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
    if isinstance(exc, ToolValidationError):
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "errors": exc.errors},
        ) from exc
    if isinstance(exc, ToolRuntimeError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.exception("Agent 工具%s失败", operation)
    raise HTTPException(
        status_code=500,
        detail=f"Agent 工具{operation}失败",
    ) from exc


def create_agent_tools_router(
    dispatcher,
    current_user_dependency: Callable[..., Any],
    user_tool_upload_service: UserToolUploadService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/chatai/agent/tools", tags=["Agent Tools"])
    upload_service = user_tool_upload_service or UserToolUploadService(
        dispatcher.repository
    )

    @router.post("")
    async def upload_agent_tool(
        file: UploadFile = File(...),
        tools_name: str = Form(...),
        display_name: str = Form(...),
        description: str = Form(...),
        platform: str = Form("all"),
        current_user: dict = Depends(current_user_dependency),
    ):
        try:
            content = await file.read(MAX_TOOL_FILE_BYTES + 1)
        finally:
            await file.close()
        metadata = UserToolUploadMetadata(
            tools_name=tools_name.strip(),
            display_name=display_name.strip(),
            description=description.strip(),
            platform=platform.strip().lower(),
        )
        try:
            result = await upload_service.upload(
                user_id=current_user["id"],
                original_filename=file.filename or "",
                content=content,
                metadata=metadata,
            )
            logger.info(
                "用户 Agent 工具上传成功，user_id=%s tool=%s",
                current_user["id"],
                metadata.tools_name,
            )
            return _success("Agent 工具上传并校验成功，当前保持禁用", result)
        except ToolValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Agent 工具校验失败",
                    "errors": exc.errors,
                },
            ) from exc
        except ToolConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (ToolStorageError, ToolRepositoryError) as exc:
            _raise_http_error("上传", exc)

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

    @router.get("/example")
    async def get_agent_tool_example_route(
        current_user: dict = Depends(current_user_dependency),
    ):
        del current_user
        try:
            return _success(
                "Agent 工具示例获取成功",
                get_agent_tool_example(),
            )
        except OSError as exc:
            _raise_http_error("示例读取", exc)

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
            ToolRuntimeError,
            ToolValidationError,
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
