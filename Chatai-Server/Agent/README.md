# Agent Python 工具模块

本目录负责固定 Python 工具的注册、校验和执行，并通过 `AgentRunner`
完成有限步的模型决策与工具调度。HTTP 流式响应和普通消息入库仍由
`Server/server.py` 负责。

## 固定边界

- 模型只能提交已注册的 `tool_name` 和 JSON 参数。
- 不执行模型生成的 Python、PowerShell、CMD 或 Shell 文本。
- 系统工具不使用数据库模块名动态导入；用户工具只允许从受控存储目录按数据库
  记录加载，并且只能在独立子进程中导入。
- 不注册 `executable` 和 `system_command` 类型工具。
- 文件工具必须通过 `allowed_roots_json` 路径校验。
- `allowed_roots_json` 为 `[]` 时拒绝路径访问，为 `["*"]` 时允许访问服务
  进程账号可访问的任意路径；`"*"` 不能和具体根目录混用。
- Agent 模式下，所有用户默认可调用 `agent_tools` 中已启用的 Python 工具，
  不依赖 `agent_tool_bindings` 用户绑定记录。
- `source_kind='system'` 的系统工具对所有用户可见，但不能由普通用户修改或删除。
- `source_kind='user'` 的用户工具只对 `owner_user_id` 对应的用户可见；删除采用
  `deleted_at` 软删除，保留 `agent_tool_runs` 审计记录。
- 用户工具支持单文件上传、AST 静态校验、独立进程运行时校验、Schema 提取、
  SHA-256 完整性校验和独立进程执行。新工具默认禁用，启用成功后才进入模型
  Schema，任何时候都不会动态导入主进程。
- `confirmation_granted` 只能由后端可信的用户确认流程设置，不能采用模型参数。

## 入口

```python
from Agent import create_default_dispatcher
from Data.db_manager import db_manager

dispatcher = create_default_dispatcher(db_manager)

# 由服务启动流程显式调用一次；该调用会同步工具描述和 JSON Schema。
await dispatcher.sync_registered_tools()

# 返回系统中所有已启用的 Python 工具 Schema；user_id 保留用于兼容现有调用。
schemas = await dispatcher.model_schemas_for_user(user_id=3)

result = await dispatcher.execute(
    user_id=3,
    conversation_id=25,
    tool_name="get_current_time",
    arguments={},
)
```

## AgentRunner

`AgentRunner` 不直接依赖具体模型，也不写入普通消息表。调用方分别传入：

- `complete_model`：收集一次结构化工具决策。
- `stream_model`：流式生成最终用户回答。

Runner 只允许模型返回 `tool` 或 `final` 两种 JSON 决策，非法 JSON 最多重试
两次，工具循环默认最多五步。工具执行仍统一经过 `ToolDispatcher`，因此工具
不存在、系统禁用、参数不合法、路径越界和执行超时都不会绕过原有保护。
`agent_tool_bindings` 表目前仅为兼容旧数据库保留，不参与工具发现和执行授权。

## 大结果策略

文本名称与目录条目的比较统一使用 `compare_path_names`，由 Python 完成名称
规范化、扫描和集合匹配。工具只向模型返回统计信息和最多20条样本；用户明确
要求全部结果时，通过 `export_full_result=true` 把完整匹配项写入服务端 CSV，
聊天正文仍不展开超大列表。`has_more`、`result_complete`、`result_file` 和
`result_download_url` 用于区分样本、完整性、服务端文件和受鉴权保护的下载地址。

进程工具使用 `psutil`。没有安装时，只有进程类工具会返回清晰错误，不影响其他工具注册和运行。
