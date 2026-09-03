import json
import sys
from pathlib import Path

from Agent.user_tools.contract import UserToolUploadMetadata
from Agent.user_tools.validator import validate_user_tool_source


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise ValueError("缺少待校验的工具文件路径")
        metadata_data = json.loads(sys.stdin.read())
        metadata = UserToolUploadMetadata(**metadata_data)
        source = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
        report = validate_user_tool_source(source, metadata)
        print(json.dumps(report.to_dict(), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "errors": [f"校验进程异常：{exc}"],
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
