from pathlib import Path


EXAMPLE_FILENAME = "count_directories.py"
EXAMPLE_FORM_DEFAULTS = {
    "tools_name": "count_directories",
    "display_name": "统计目录数量",
    "description": "统计指定目录下一级子目录的数量",
    "platform": "all",
}
def get_agent_tool_example() -> dict:
    source_path = Path(__file__).with_name(EXAMPLE_FILENAME)
    return {
        "filename": EXAMPLE_FILENAME,
        "source": source_path.read_text(encoding="utf-8"),
    }
