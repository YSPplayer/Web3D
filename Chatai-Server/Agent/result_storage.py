import re
import uuid
from pathlib import Path

from Config.config import config


RESULT_FILENAME_PATTERN = re.compile(
    r"name_comparison_[0-9a-f]{32}\.csv"
)


def create_name_comparison_result(user_id: int) -> tuple[Path, str]:
    filename = f"name_comparison_{uuid.uuid4().hex}.csv"
    directory = config.log_path / "agent_results" / f"user_{user_id}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    return path, f"/chatai/agent/results/{filename}"


def resolve_user_result(user_id: int, filename: str) -> Path | None:
    if RESULT_FILENAME_PATTERN.fullmatch(filename) is None:
        return None
    directory = (
        config.log_path / "agent_results" / f"user_{user_id}"
    ).resolve()
    path = (directory / filename).resolve()
    if path.parent != directory or not path.is_file():
        return None
    return path
