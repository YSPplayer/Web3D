from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

from Agent.context import ToolContext


ArgumentsType = TypeVar("ArgumentsType", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    display_name: str
    description: str
    platform: str
    input_schema: dict
    risk_level: str
    requires_confirmation: bool
    timeout_seconds: int
    max_output_bytes: int


class PythonTool(ABC, Generic[ArgumentsType]):
    name: str
    display_name: str
    description: str
    args_model: type[ArgumentsType]

    platform = "all"
    risk_level = "low"
    requires_confirmation = False
    timeout_seconds = 10
    max_output_bytes = 65_536

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            platform=self.platform,
            input_schema=self.args_model.model_json_schema(),
            risk_level=self.risk_level,
            requires_confirmation=self.requires_confirmation,
            timeout_seconds=self.timeout_seconds,
            max_output_bytes=self.max_output_bytes,
        )

    def model_schema(self) -> dict:
        definition = self.definition()
        return {
            "type": "function",
            "function": {
                "name": definition.name,
                "description": definition.description,
                "parameters": definition.input_schema,
            },
        }

    @abstractmethod
    async def execute(
        self,
        context: ToolContext,
        arguments: ArgumentsType,
    ) -> dict:
        raise NotImplementedError
