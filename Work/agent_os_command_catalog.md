# Agent OS 工具清单与 SQLite 入库格式

本文档用于整理 ChatAI Agent 可以开放给模型使用的公共系统工具。核心原则是：模型只输出 JSON 工具调用意图，后端只执行白名单工具，禁止把模型输出直接当作 Windows/Linux 控制台命令执行。

## 1. 总体执行边界

正确链路：

```text
用户输入
  -> 后端 Agent 生成工具说明 Prompt
  -> 模型输出 JSON 工具调用意图
  -> 后端校验 tool_name 和 arguments
  -> 后端根据数据库中的工具配置调度 Python/EXE/系统能力
  -> 工具返回结构化 JSON
  -> 后端把工具结果交回模型
  -> 模型生成最终回答
```

禁止链路：

```text
模型输出 cmd / powershell / bash 字符串
  -> 后端直接 shell=True 执行
```

原因：

- 容易被提示词注入诱导执行危险命令。
- 无法可靠限制文件路径、参数、超时、输出大小。
- 无法做审计和用户确认。
- Windows/Linux 命令语法不同，直接暴露给模型会导致不可控行为。

## 2. Agent 统一 JSON 协议

### 2.1 模型请求调用工具

```json
{
  "type": "tool_call",
  "tool": "list_directory",
  "arguments": {
    "path": "D:/YueShaoPu/Web3D",
    "max_depth": 1
  }
}
```

### 2.2 模型输出最终回答

```json
{
  "type": "final",
  "content": "已经查询完成，目录中包含 Chatai、Chatai-Server、Work 等模块。"
}
```

### 2.3 后端返回工具结果给模型

```json
{
  "type": "tool_result",
  "tool": "list_directory",
  "result": {
    "items": [
      {
        "name": "Chatai",
        "type": "directory"
      },
      {
        "name": "Chatai-Server",
        "type": "directory"
      }
    ]
  }
}
```

## 3. 工具定义 JSON 格式

数据库中建议保存工具定义，Python 启动时加载 enabled 工具，动态生成 Agent Prompt。

```json
{
  "tools_name": "list_directory",
  "display_name": "列出目录",
  "description": "列出允许目录下的文件和文件夹，不读取文件内容。",
  "tool_type": "python_builtin",
  "platform": "all",
  "executable_path": "",
  "working_dir": "",
  "argv_template": [],
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "要列出的目录路径，必须位于 allowed_roots 中。"
      },
      "max_depth": {
        "type": "integer",
        "minimum": 0,
        "maximum": 3,
        "default": 1
      }
    },
    "required": ["path"]
  },
  "allowed_roots": [
    "D:/YueShaoPu/Web3D"
  ],
  "is_enabled": 1,
  "requires_confirmation": 0,
  "risk_level": "low",
  "timeout_seconds": 10,
  "max_output_bytes": 65536
}
```

说明：

- `tools_name` 是模型可见的工具名。
- `display_name` 是前端展示名。
- `description` 会进入 Agent Prompt。
- `tool_type` 推荐取值：`python_builtin`、`executable`、`system_command`。
- `platform` 推荐取值：`windows`、`linux`、`all`。
- `argv_template` 必须是 JSON 数组，不允许保存整条 shell 字符串。
- `input_schema` 使用 JSON Schema 风格描述参数。
- `allowed_roots` 用于限制文件访问范围。
- `requires_confirmation=1` 表示前端必须弹确认框。
- `risk_level=high` 的工具默认不建议开放给模型自动调用。

## 4. 推荐开放的公共 OS 工具清单

这些工具是“AI 常用能力”的抽象接口。Windows/Linux 命令只是后端实现参考，不应直接暴露给模型。

| 工具名 | 用途 | Windows 实现参考 | Linux 实现参考 | 风险 |
|---|---|---|---|---|
| `get_current_time` | 获取当前时间 | `Get-Date` | `date` | low |
| `get_hostname` | 获取主机名 | `hostname` | `hostname` | low |
| `get_current_user` | 获取当前用户名 | `whoami` | `whoami` / `id -un` | low |
| `get_os_info` | 获取系统版本 | `Get-ComputerInfo` / `systeminfo` | `uname -a` / `lsb_release -a` | low |
| `list_directory` | 列出目录 | `Get-ChildItem -LiteralPath` | `find` / `ls` | low |
| `file_stat` | 查看文件元信息 | `Get-Item` | `stat` | low |
| `read_text_file` | 读取文本文件 | `Get-Content -Raw` | `cat` / `sed` | medium |
| `read_file_head` | 读取文件开头 | `Get-Content -TotalCount` | `head` | low |
| `read_file_tail` | 读取文件结尾 | `Get-Content -Tail` | `tail` | low |
| `find_files` | 按文件名查找 | `Get-ChildItem -Recurse -Filter` | `find -name` | low |
| `search_text` | 搜索文本内容 | `Select-String` | `grep -R` / `rg` | medium |
| `get_disk_usage` | 查看磁盘空间 | `Get-PSDrive` | `df -h` | low |
| `get_directory_size` | 查看目录大小 | `Get-ChildItem + Measure-Object` | `du -sh` | medium |
| `get_process_list` | 查看进程列表 | `Get-Process` | `ps aux` | low |
| `get_process_detail` | 查看指定进程 | `Get-Process -Id` | `ps -p` | low |
| `kill_process` | 结束指定进程 | `Stop-Process -Id` | `kill` | high |
| `ping_host` | 测试主机连通性 | `Test-Connection` | `ping -c` | low |
| `check_tcp_port` | 检测端口 | `Test-NetConnection` | `nc -zv` / `ss` | low |
| `http_get` | HTTP GET 请求 | `Invoke-WebRequest` | `curl` | medium |
| `run_executable` | 调用预注册 EXE | `CreateProcess` / `subprocess_exec` | `execve` / `subprocess_exec` | high |

## 5. 建议默认开放的低风险工具

第一阶段建议只开放这些：

```text
get_current_time
get_hostname
get_current_user
get_os_info
list_directory
file_stat
read_file_head
read_file_tail
find_files
get_disk_usage
get_process_list
ping_host
check_tcp_port
```

第二阶段再开放：

```text
read_text_file
search_text
get_directory_size
http_get
run_executable
```

默认不自动开放：

```text
kill_process
write_file
delete_file
move_file
copy_file
install_package
change_permission
service_start_stop
registry_write
shutdown_or_reboot
```

## 6. 禁止直接开放的系统命令

这些命令即使要支持，也必须封装成受限工具，并要求用户确认。

### 6.1 Windows 高风险命令

```text
del
rmdir
format
shutdown
reg add
reg delete
sc stop
sc delete
net user
net localgroup
powershell -Command 任意字符串
cmd /c 任意字符串
Start-Process 任意路径
```

### 6.2 Linux 高风险命令

```text
rm
mv
chmod
chown
dd
mkfs
shutdown
reboot
systemctl stop
systemctl disable
useradd
passwd
sudo 任意命令
bash -c 任意字符串
curl ... | bash
wget ... | sh
```

## 7. 推荐 SQLite 表结构

当前项目使用 SQLite。JSON 字段建议用 `TEXT` 存储。

如果 `run.sql` 已经存在旧表，`CREATE TABLE IF NOT EXISTS` 不会自动迁移旧字段。后续正式落库时需要单独写 `ALTER TABLE` 或手动重建表。

### 7.1 agent_tools

```sql
CREATE TABLE IF NOT EXISTS agent_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tools_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',

    tool_type TEXT NOT NULL DEFAULT 'python_builtin'
        CHECK (tool_type IN ('python_builtin', 'executable', 'system_command')),

    platform TEXT NOT NULL DEFAULT 'all'
        CHECK (platform IN ('windows', 'linux', 'all')),

    executable_path TEXT NOT NULL DEFAULT '',
    working_dir TEXT NOT NULL DEFAULT '',

    argv_template_json TEXT NOT NULL DEFAULT '[]',
    input_schema_json TEXT NOT NULL DEFAULT '{}',
    allowed_roots_json TEXT NOT NULL DEFAULT '[]',

    is_enabled INTEGER NOT NULL DEFAULT 1
        CHECK (is_enabled IN (0, 1)),

    requires_confirmation INTEGER NOT NULL DEFAULT 0
        CHECK (requires_confirmation IN (0, 1)),

    risk_level TEXT NOT NULL DEFAULT 'low'
        CHECK (risk_level IN ('low', 'medium', 'high')),

    timeout_seconds INTEGER NOT NULL DEFAULT 30,
    max_output_bytes INTEGER NOT NULL DEFAULT 65536,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 7.2 agent_tool_bindings

用户可以按需启用/禁用工具。

```sql
CREATE TABLE IF NOT EXISTS agent_tool_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,

    is_enabled INTEGER NOT NULL DEFAULT 1
        CHECK (is_enabled IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES agent_tools(id) ON DELETE CASCADE,

    UNIQUE(user_id, tool_id)
);
```

### 7.3 agent_tool_runs

用于审计每一次工具调用。

```sql
CREATE TABLE IF NOT EXISTS agent_tool_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    conversation_id INTEGER,
    tool_id INTEGER NOT NULL,

    tools_name TEXT NOT NULL,
    arguments_json TEXT NOT NULL DEFAULT '{}',

    status TEXT NOT NULL
        CHECK (status IN ('running', 'success', 'failed', 'timeout', 'denied')),

    exit_code INTEGER,
    result_json TEXT,
    stdout_text TEXT,
    stderr_text TEXT,
    error_message TEXT,

    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (tool_id) REFERENCES agent_tools(id) ON DELETE CASCADE
);
```

## 8. 可写入 run.sql 的基础工具插入格式

下面示例使用 `INSERT OR IGNORE`，适合放到 `Chatai-Server/Sql/run.sql` 中。

### 8.1 get_current_time

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'get_current_time',
    '获取当前时间',
    '获取当前操作系统时间，用于回答当前日期、时间、时间戳等问题。',
    'python_builtin',
    'all',
    '',
    '',
    '[]',
    '{"type":"object","properties":{},"required":[]}',
    '[]',
    1,
    0,
    'low',
    5,
    4096,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 8.2 list_directory

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'list_directory',
    '列出目录',
    '列出允许目录下的文件和文件夹，不读取文件内容。',
    'python_builtin',
    'all',
    '',
    '',
    '[]',
    '{"type":"object","properties":{"path":{"type":"string"},"max_depth":{"type":"integer","minimum":0,"maximum":3,"default":1}},"required":["path"]}',
    '["D:/YueShaoPu/Web3D"]',
    1,
    0,
    'low',
    10,
    65536,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 8.3 read_text_file

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'read_text_file',
    '读取文本文件',
    '读取允许目录下的文本文件内容。需要限制最大输出长度。',
    'python_builtin',
    'all',
    '',
    '',
    '[]',
    '{"type":"object","properties":{"path":{"type":"string"},"encoding":{"type":"string","default":"utf-8"},"max_bytes":{"type":"integer","minimum":1,"maximum":65536,"default":20000}},"required":["path"]}',
    '["D:/YueShaoPu/Web3D"]',
    1,
    0,
    'medium',
    10,
    65536,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 8.4 search_text

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'search_text',
    '搜索文本',
    '在允许目录下按关键字搜索文本，优先由后端使用 rg 或平台原生命令实现。',
    'python_builtin',
    'all',
    '',
    '',
    '[]',
    '{"type":"object","properties":{"path":{"type":"string"},"pattern":{"type":"string"},"case_sensitive":{"type":"boolean","default":false},"max_results":{"type":"integer","minimum":1,"maximum":100,"default":20}},"required":["path","pattern"]}',
    '["D:/YueShaoPu/Web3D"]',
    1,
    0,
    'medium',
    15,
    65536,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 8.5 get_process_list

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'get_process_list',
    '获取进程列表',
    '获取当前系统进程列表，只返回进程名、PID、CPU/内存摘要，不包含敏感环境变量。',
    'python_builtin',
    'all',
    '',
    '',
    '[]',
    '{"type":"object","properties":{"keyword":{"type":"string","default":""},"limit":{"type":"integer","minimum":1,"maximum":100,"default":50}},"required":[]}',
    '[]',
    1,
    0,
    'low',
    10,
    65536,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 8.6 ping_host

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'ping_host',
    'Ping 主机',
    '测试指定主机是否可达。后端必须限制超时时间和次数。',
    'python_builtin',
    'all',
    '',
    '',
    '[]',
    '{"type":"object","properties":{"host":{"type":"string"},"count":{"type":"integer","minimum":1,"maximum":4,"default":2}},"required":["host"]}',
    '[]',
    1,
    0,
    'low',
    10,
    32768,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 8.7 run_registered_executable

这个工具用于调用预注册 EXE。它风险较高，建议默认要求用户确认。

```sql
INSERT OR IGNORE INTO agent_tools (
    tools_name,
    display_name,
    description,
    tool_type,
    platform,
    executable_path,
    working_dir,
    argv_template_json,
    input_schema_json,
    allowed_roots_json,
    is_enabled,
    requires_confirmation,
    risk_level,
    timeout_seconds,
    max_output_bytes,
    created_at,
    updated_at
) VALUES (
    'run_registered_executable',
    '运行预注册程序',
    '运行后端预注册的本地 EXE。模型只能传参数，不能传 exe 路径。',
    'executable',
    'windows',
    'D:/YueShaoPu/Web3D/tools/example.exe',
    'D:/YueShaoPu/Web3D/tools',
    '["--input", "{input_file}", "--mode", "{mode}"]',
    '{"type":"object","properties":{"input_file":{"type":"string"},"mode":{"type":"string","enum":["fast","accurate"]}},"required":["input_file","mode"]}',
    '["D:/YueShaoPu/Web3D/Chatai-Server/Data"]',
    0,
    1,
    'high',
    60,
    65536,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

## 9. 后端调度约束

Python 调度层必须满足：

```text
1. 只能执行数据库中 is_enabled=1 的工具。
2. 用户必须在 agent_tool_bindings 中启用该工具。
3. 参数必须通过 input_schema_json 校验。
4. 文件路径必须位于 allowed_roots_json 中。
5. executable_path 只能来自数据库，不能来自模型输出。
6. subprocess 必须使用 shell=False。
7. argv 必须由 argv_template_json 数组生成，不能拼接成整条命令字符串。
8. 每次调用必须写入 agent_tool_runs。
9. high 风险工具必须前端确认。
10. stdout/stderr 必须限制 max_output_bytes。
```

## 10. Python 调度伪代码

```python
async def run_agent_tool(user_id: int, conversation_id: int, tool_name: str, arguments: dict):
    tool = db_manager.get_enabled_agent_tool(user_id, tool_name)
    if not tool:
        return {"status": "denied", "error": "工具不存在或未启用"}

    validate_json_schema(arguments, tool["input_schema_json"])
    validate_allowed_roots(arguments, tool["allowed_roots_json"])

    if tool["requires_confirmation"] == 1:
        return {"status": "need_confirmation", "tool": tool_name}

    if tool["tool_type"] == "python_builtin":
        return await builtin_tool_registry.call(tool_name, arguments)

    if tool["tool_type"] == "executable":
        argv = build_argv_from_template(
            tool["argv_template_json"],
            arguments
        )
        return await run_executable(
            executable_path=tool["executable_path"],
            working_dir=tool["working_dir"],
            argv=argv,
            timeout_seconds=tool["timeout_seconds"],
            max_output_bytes=tool["max_output_bytes"]
        )

    return {"status": "failed", "error": "不支持的工具类型"}
```

## 11. 给模型的 Prompt 工具声明示例

后端可以把数据库中的 enabled 工具转换成如下 Prompt：

```text
你是一个本地 Agent。你不能直接输出 Windows/Linux 命令。
你只能调用下面白名单工具。

工具：
1. list_directory
说明：列出允许目录下的文件和文件夹。
参数 JSON Schema：
{"type":"object","properties":{"path":{"type":"string"},"max_depth":{"type":"integer","minimum":0,"maximum":3}},"required":["path"]}

2. read_text_file
说明：读取允许目录下的文本文件内容。
参数 JSON Schema：
{"type":"object","properties":{"path":{"type":"string"},"max_bytes":{"type":"integer","maximum":65536}},"required":["path"]}

如果需要工具，只能返回：
{"type":"tool_call","tool":"工具名","arguments":{}}

如果可以直接回答，只能返回：
{"type":"final","content":"回答内容"}
```

## 12. 第一阶段建议落地顺序

```text
1. 先把 agent_tools / agent_tool_bindings / agent_tool_runs 表结构补齐。
2. 先注册 get_current_time、list_directory、file_stat 三个低风险工具。
3. 后端实现 AgentToolManager。
4. 前端配置页增加工具开关和风险提示。
5. 跑通 JSON Agent 调用链路。
6. 再开放 read_text_file、search_text。
7. 最后才开放 run_registered_executable。
```
