# Agent Python 工具模块

本目录只负责固定 Python 工具的注册、校验和执行，不负责聊天接口或模型循环。

## 固定边界

- 模型只能提交已注册的 `tool_name` 和 JSON 参数。
- 不执行模型生成的 Python、PowerShell、CMD 或 Shell 文本。
- 不使用数据库中的模块名动态导入 Python 代码。
- 不注册 `executable` 和 `system_command` 类型工具。
- 文件工具必须通过 `allowed_roots_json` 路径校验。
- 数据库没有 `agent_tool_bindings` 记录时，用户默认无权调用工具。
- `confirmation_granted` 只能由后端可信的用户确认流程设置，不能采用模型参数。

## 入口

```python
from Agent import create_default_dispatcher
from Data.db_manager import db_manager

dispatcher = create_default_dispatcher(db_manager)

# 由服务启动流程显式调用一次；该调用会同步工具描述和 JSON Schema。
await dispatcher.sync_registered_tools()

# 只返回当前用户已绑定且已启用的工具 Schema。
schemas = await dispatcher.model_schemas_for_user(user_id=3)

result = await dispatcher.execute(
    user_id=3,
    conversation_id=25,
    tool_name="get_current_time",
    arguments={},
)
```

用户工具授权通过仓储显式设置：

```python
from Data.agent_tool_repository import AgentToolRepository

repository = AgentToolRepository(db_manager)
repository.set_user_tool_binding(3, "get_current_time", True)
```

进程工具使用 `psutil`。没有安装时，只有进程类工具会返回清晰错误，不影响其他工具注册和运行。
