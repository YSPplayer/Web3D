from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from Agent.result_storage import resolve_user_result


def create_agent_results_router(
    current_user_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(
        prefix="/chatai/agent/results",
        tags=["Agent Results"],
    )

    @router.get("/{filename}")
    async def download_agent_result(
        filename: str,
        current_user: dict = Depends(current_user_dependency),
    ):
        path = resolve_user_result(current_user["id"], filename)
        if path is None:
            raise HTTPException(status_code=404, detail="结果文件不存在")
        return FileResponse(
            path,
            media_type="text/csv",
            filename=path.name,
        )

    return router
