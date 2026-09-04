import ast
import asyncio
import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext
from Agent.tool_policy import resolve_allowed_path


class ValidationFileArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    encoding: str = "utf-8"
    max_bytes: int = Field(default=2 * 1024 * 1024, ge=1, le=10 * 1024 * 1024)


class SqliteSchemaArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    max_tables: int = Field(default=100, ge=1, le=500)


def _read_limited_text(path: Path, encoding: str, max_bytes: int) -> str:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"文件大小 {size} 字节，超过 max_bytes 限制")
    return path.read_text(encoding=encoding)


class ValidatePythonSyntaxTool(PythonTool[ValidationFileArguments]):
    name = "validate_python_syntax"
    display_name = "校验 Python 语法"
    description = "使用 Python AST 解析允许范围内的 .py 文件，不执行文件代码。"
    args_model = ValidationFileArguments
    timeout_seconds = 15
    max_output_bytes = 16_384

    async def execute(self, context: ToolContext, arguments: ValidationFileArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)
        if path.suffix.casefold() not in {".py", ".pyw"}:
            raise ValueError("只允许校验 .py 或 .pyw 文件")

        def validate() -> dict:
            source = _read_limited_text(path, arguments.encoding, arguments.max_bytes)
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError as exc:
                return {
                    "path": str(path),
                    "valid": False,
                    "error": exc.msg,
                    "line": exc.lineno,
                    "column": exc.offset,
                    "text": exc.text.rstrip("\r\n") if exc.text else None,
                }
            return {
                "path": str(path),
                "valid": True,
                "top_level_nodes": len(tree.body),
            }

        return await asyncio.to_thread(validate)


class ValidateJsonTool(PythonTool[ValidationFileArguments]):
    name = "validate_json"
    display_name = "校验 JSON"
    description = "解析允许范围内的 JSON 文件并返回准确错误位置，不修改文件。"
    args_model = ValidationFileArguments
    timeout_seconds = 15
    max_output_bytes = 16_384

    async def execute(self, context: ToolContext, arguments: ValidationFileArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)

        def validate() -> dict:
            source = _read_limited_text(path, arguments.encoding, arguments.max_bytes)
            try:
                value = json.loads(source)
            except json.JSONDecodeError as exc:
                return {
                    "path": str(path),
                    "valid": False,
                    "error": exc.msg,
                    "line": exc.lineno,
                    "column": exc.colno,
                    "position": exc.pos,
                }
            if isinstance(value, dict):
                value_type = "object"
                item_count = len(value)
            elif isinstance(value, list):
                value_type = "array"
                item_count = len(value)
            else:
                value_type = type(value).__name__
                item_count = None
            return {
                "path": str(path),
                "valid": True,
                "root_type": value_type,
                "item_count": item_count,
            }

        return await asyncio.to_thread(validate)


class InspectSqliteSchemaTool(PythonTool[SqliteSchemaArguments]):
    name = "inspect_sqlite_schema"
    display_name = "查看 SQLite 结构"
    description = "以只读模式查看 SQLite 数据库的表、字段、索引和外键，不读取业务记录。"
    args_model = SqliteSchemaArguments
    risk_level = "medium"
    timeout_seconds = 30
    max_output_bytes = 262_144

    async def execute(self, context: ToolContext, arguments: SqliteSchemaArguments) -> dict:
        path = resolve_allowed_path(arguments.path, context.allowed_roots, must_exist=True, require_file=True)

        def inspect() -> dict:
            uri = path.as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True, timeout=5)
            connection.row_factory = sqlite3.Row
            try:
                table_rows = connection.execute(
                    """
                    SELECT name, type
                    FROM sqlite_master
                    WHERE type IN ('table', 'view')
                      AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    LIMIT ?
                    """,
                    (arguments.max_tables + 1,),
                ).fetchall()
                truncated = len(table_rows) > arguments.max_tables
                tables = []
                for table in table_rows[: arguments.max_tables]:
                    quoted = table["name"].replace("'", "''")
                    columns = [dict(row) for row in connection.execute(f"PRAGMA table_info('{quoted}')")]
                    indexes = [dict(row) for row in connection.execute(f"PRAGMA index_list('{quoted}')")]
                    foreign_keys = [dict(row) for row in connection.execute(f"PRAGMA foreign_key_list('{quoted}')")]
                    tables.append({
                        "name": table["name"],
                        "type": table["type"],
                        "columns": columns,
                        "indexes": indexes,
                        "foreign_keys": foreign_keys,
                    })
                return {
                    "path": str(path),
                    "tables": tables,
                    "table_count": len(tables),
                    "truncated": truncated,
                }
            finally:
                connection.close()

        return await asyncio.to_thread(inspect)
