PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar_base64 TEXT DEFAULT '',
    avatar_mime TEXT NOT NULL DEFAULT 'image/png',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    model_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    api_key TEXT NOT NULL,
    is_online INTEGER NOT NULL DEFAULT 1
        CHECK (is_online IN (0, 1)),
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    model_config_id INTEGER NOT NULL,
    title TEXT NOT NULL DEFAULT '新对话',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (model_config_id)
        REFERENCES model_configs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id
ON conversations(user_id);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    role TEXT NOT NULL
        CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL DEFAULT '',
    tokens_used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id)
        REFERENCES models(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_type TEXT NOT NULL,
    model_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    logo_path TEXT NOT NULL
);
INSERT OR IGNORE INTO models (id, provider_type, model_type, model_name, logo_path) VALUES
(1,  'zai',       'glm',      'glm-4-plus',                     'logo/glm.svg'),
(2,  'zai',       'glm',      'glm-4-air',                      'logo/glm.svg'),
(3,  'zai',       'glm',      'glm-4-flash',                    'logo/glm.svg'),
(4,  'zai',       'glm',      'glm-5.2',                        'logo/glm.svg'),
(5,  'openai',    'gpt',      'gpt-4o',                         'logo/openai.svg'),
(6,  'openai',    'gpt',      'gpt-4o-mini',                    'logo/openai.svg'),
(7,  'openai',    'gpt',      'gpt-3.5-turbo',                  'logo/openai.svg'),
(8,  'anthropic', 'claude',   'claude-3-5-sonnet-latest',       'logo/anthropic.svg'),
(9,  'anthropic', 'claude',   'claude-3-haiku-latest',          'logo/anthropic.svg'),
(10, 'anthropic', 'claude',   'claude-3-opus-latest',           'logo/anthropic.svg'),
(11, 'deepseek',  'deepseek', 'deepseek-chat',                  'logo/deepseek.svg'),
(12, 'deepseek',  'deepseek', 'deepseek-coder',                 'logo/deepseek.svg'),
(13, 'local',     'local',    'DeepSeek-R1-Distill-Qwen-7B',    'logo/deepqwen.svg'),
(14, 'local',     'local',    'Qwen2.5-Coder-3B-Instruct',      'logo/deepqwen.svg');

UPDATE model_configs
SET is_online = 0
WHERE model_type = 'local';

UPDATE model_configs
SET is_online = 1
WHERE model_type != 'local';

CREATE TABLE IF NOT EXISTS proxy_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    proxy_host TEXT NOT NULL,
    proxy_port INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0
        CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);
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

CREATE INDEX IF NOT EXISTS idx_agent_tool_runs_user_id
ON agent_tool_runs(user_id);

CREATE INDEX IF NOT EXISTS idx_agent_tool_runs_conversation_id
ON agent_tool_runs(conversation_id);

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
) VALUES
('get_current_time', '获取当前时间', '获取当前操作系统时间，用于回答当前日期、时间、时间戳等问题。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{},"required":[]}', '[]', 1, 0, 'low', 5, 4096, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_hostname', '获取主机名', '获取当前计算机主机名。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{},"required":[]}', '[]', 1, 0, 'low', 5, 4096, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_current_user', '获取当前用户', '获取当前操作系统登录用户名称。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{},"required":[]}', '[]', 1, 0, 'low', 5, 4096, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_os_info', '获取系统信息', '获取当前操作系统版本、内核、架构等基础信息。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{},"required":[]}', '[]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('list_directory', '列出目录', '列出允许目录下的文件和文件夹，不读取文件内容。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"max_depth":{"type":"integer","minimum":0,"maximum":3,"default":1}},"required":["path"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'low', 10, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('file_stat', '查看文件信息', '查看允许目录下文件或文件夹的大小、修改时间、类型等元信息。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('read_text_file', '读取文本文件', '读取允许目录下的文本文件内容，需要限制最大输出长度。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"encoding":{"type":"string","default":"utf-8"},"max_bytes":{"type":"integer","minimum":1,"maximum":65536,"default":20000}},"required":["path"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'medium', 10, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('read_file_head', '读取文件开头', '读取允许目录下文本文件的前 N 行。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"lines":{"type":"integer","minimum":1,"maximum":200,"default":50},"encoding":{"type":"string","default":"utf-8"}},"required":["path"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('read_file_tail', '读取文件结尾', '读取允许目录下文本文件的最后 N 行，常用于查看日志。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"lines":{"type":"integer","minimum":1,"maximum":200,"default":50},"encoding":{"type":"string","default":"utf-8"}},"required":["path"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('find_files', '查找文件', '在允许目录下按文件名或通配符查找文件。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"pattern":{"type":"string"},"max_results":{"type":"integer","minimum":1,"maximum":200,"default":50}},"required":["path","pattern"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'low', 15, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('search_text', '搜索文本', '在允许目录下按关键字搜索文本，优先由后端使用 rg 或平台原生命令实现。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"pattern":{"type":"string"},"case_sensitive":{"type":"boolean","default":false},"max_results":{"type":"integer","minimum":1,"maximum":100,"default":20}},"required":["path","pattern"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'medium', 15, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_disk_usage', '查看磁盘空间', '查看磁盘容量、已用空间、可用空间。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string","default":""}},"required":[]}', '[]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_directory_size', '查看目录大小', '统计允许目录下指定目录的大小。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"path":{"type":"string"},"max_depth":{"type":"integer","minimum":0,"maximum":5,"default":3}},"required":["path"]}', '["D:/YueShaoPu/Web3D"]', 1, 0, 'medium', 30, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_process_list', '获取进程列表', '获取当前系统进程列表，只返回进程名、PID、CPU/内存摘要，不包含敏感环境变量。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"keyword":{"type":"string","default":""},"limit":{"type":"integer","minimum":1,"maximum":100,"default":50}},"required":[]}', '[]', 1, 0, 'low', 10, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('get_process_detail', '获取进程详情', '按 PID 获取指定进程的基础详情。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"pid":{"type":"integer","minimum":1}},"required":["pid"]}', '[]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('kill_process', '结束进程', '结束指定 PID 的进程。高风险工具，默认禁用且需要用户确认。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"pid":{"type":"integer","minimum":1}},"required":["pid"]}', '[]', 0, 1, 'high', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('ping_host', 'Ping 主机', '测试指定主机是否可达。后端必须限制超时时间和次数。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"host":{"type":"string"},"count":{"type":"integer","minimum":1,"maximum":4,"default":2}},"required":["host"]}', '[]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('check_tcp_port', '检测 TCP 端口', '检测指定主机和端口是否可连接。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"host":{"type":"string"},"port":{"type":"integer","minimum":1,"maximum":65535},"timeout_seconds":{"type":"integer","minimum":1,"maximum":10,"default":3}},"required":["host","port"]}', '[]', 1, 0, 'low', 10, 32768, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('http_get', 'HTTP GET 请求', '向指定 URL 发起 GET 请求并返回状态码和有限响应内容。', 'python_builtin', 'all', '', '', '[]', '{"type":"object","properties":{"url":{"type":"string"},"timeout_seconds":{"type":"integer","minimum":1,"maximum":15,"default":5},"max_bytes":{"type":"integer","minimum":1,"maximum":65536,"default":20000}},"required":["url"]}', '[]', 1, 0, 'medium', 15, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('run_registered_executable', '运行预注册程序', '运行后端预注册的本地 EXE。模型只能传参数，不能传 exe 路径。', 'executable', 'windows', 'D:/YueShaoPu/Web3D/tools/example.exe', 'D:/YueShaoPu/Web3D/tools', '["--input","{input_file}","--mode","{mode}"]', '{"type":"object","properties":{"input_file":{"type":"string"},"mode":{"type":"string","enum":["fast","accurate"]}},"required":["input_file","mode"]}', '["D:/YueShaoPu/Web3D/Chatai-Server/Data"]', 0, 1, 'high', 60, 65536, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
