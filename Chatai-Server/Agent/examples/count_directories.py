import asyncio

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(description="需要统计的目录路径")


class CountDirectoriesTool(PythonTool[Arguments]):
    name = "count_directories"
    display_name = "统计目录数量"
    description = "统计指定目录下一级子目录的数量"
    args_model = Arguments
    platform = "all"

    async def execute(
        self,
        context: ToolContext,
        arguments: Arguments,
    ) -> dict:
        directory = resolve_allowed_path(
            arguments.path,
            context.allowed_roots,
            must_exist=True,
            require_directory=True,
        )

        def scan() -> list[str]:
            return sorted(
                item.name
                for item in directory.iterdir()
                if item.is_dir()
            )

        directory_names = await asyncio.to_thread(scan)
        return {
            "path": str(directory),
            "directory_count": len(directory_names),
            "directory_names": directory_names,
        }


tool = CountDirectoriesTool()

