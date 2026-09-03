from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class UserToolUploadMetadata:
    tools_name: str
    display_name: str
    description: str
    platform: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    errors: tuple[str, ...]
    tool_class_name: str = ""
    arguments_class_name: str = ""
    entrypoint: str = ""

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "tool_class_name": self.tool_class_name,
            "arguments_class_name": self.arguments_class_name,
            "entrypoint": self.entrypoint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationReport":
        return cls(
            valid=bool(data.get("valid")),
            errors=tuple(str(item) for item in data.get("errors", [])),
            tool_class_name=str(data.get("tool_class_name", "")),
            arguments_class_name=str(data.get("arguments_class_name", "")),
            entrypoint=str(data.get("entrypoint", "")),
        )
