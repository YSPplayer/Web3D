# 用户 Python 工具上传规范

用户工具上传后会依次完成 AST 静态校验、独立进程运行时校验、Pydantic
参数 Schema 提取、落盘和数据库登记。上传文件不会被 FastAPI 主进程导入；
新工具默认禁用，用户主动启用并再次通过完整性校验后才会进入 Agent Schema。

## 文件约定

- 只允许单个 UTF-8 编码的 `.py` 文件，最大 256 KiB。
- 文件必须定义且只定义一个 `PythonTool` 子类。
- 参数模型必须继承 `pydantic.BaseModel`。
- 工具类必须实现 `async def execute(self, context, arguments) -> dict`。
- 文件末尾必须通过 `tool = ToolClass()` 导出工具实例。
- `name`、`display_name`、`description`、`platform` 必须是字符串常量，且与
  上传表单一致。
- 不允许普通模块级函数调用或其他可执行语句。

## 上传接口

```text
POST /chatai/agent/tools
Content-Type: multipart/form-data
```

字段：`file`、`tools_name`、`display_name`、`description`、`platform`。
`owner_user_id` 只从服务端认证身份获取，不接受前端传值。

## 示例

```python
from pydantic import BaseModel

from Agent.base import PythonTool
from Agent.context import ToolContext


class Arguments(BaseModel):
    value: str


class Tool(PythonTool[Arguments]):
    name = "echo_value"
    display_name = "返回输入"
    description = "返回用户传入的字符串"
    args_model = Arguments
    platform = "all"

    async def execute(
        self,
        context: ToolContext,
        arguments: Arguments,
    ) -> dict:
        return {"value": arguments.value}


tool = Tool()
```

## 运行边界

- 每次调用都在独立 Python 子进程中重新加载和执行，不导入 FastAPI 主进程。
- 启用和执行前都会校验数据库中的 SHA-256，文件被修改后将拒绝运行。
- 参数由工具自己的 Pydantic 模型校验，`execute` 必须返回 `dict`。
- 默认执行超时为 30 秒，结果最大 65536 字节；超时会终止工具子进程。
- 用户主动启用自己上传的工具视为持久授权，不再逐次要求确认。
- 子进程会移除大部分父进程环境变量，但它仍继承服务器操作系统账号的文件和
  网络权限。若要运行不可信的第三方代码，仍应进一步使用低权限账号、容器或
  Windows Sandbox 等操作系统级隔离。
