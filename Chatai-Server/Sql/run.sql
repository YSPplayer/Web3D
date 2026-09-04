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

CREATE TABLE IF NOT EXISTS auth_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    user_agent TEXT NOT NULL DEFAULT '',
    ip_address TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id
ON auth_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at
ON auth_sessions(expires_at);

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
    status TEXT NOT NULL DEFAULT 'completed'
        CHECK (status IN ('streaming', 'completed', 'cancelled', 'failed')),
    finish_reason TEXT,
    request_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    logo_path TEXT NOT NULL,
    context_window INTEGER,
    max_output_tokens INTEGER,
    safety_margin_tokens INTEGER NOT NULL DEFAULT 512
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

CREATE TABLE IF NOT EXISTS conversation_summaries (
    conversation_id INTEGER PRIMARY KEY,
    summary_text TEXT NOT NULL DEFAULT '',
    summarized_through_message_id INTEGER NOT NULL DEFAULT 0,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_usage_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    message_id INTEGER,
    model_id INTEGER NOT NULL,
    model_config_id INTEGER NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('chat', 'agent')),
    call_type TEXT NOT NULL,
    agent_step INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    context_window INTEGER NOT NULL,
    max_output_tokens INTEGER NOT NULL,
    truncated_messages INTEGER NOT NULL DEFAULT 0,
    summary_used INTEGER NOT NULL DEFAULT 0
        CHECK (summary_used IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'success'
        CHECK (status IN ('success', 'failed', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    FOREIGN KEY (model_config_id) REFERENCES model_configs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_model_usage_runs_conversation_id
ON model_usage_runs(conversation_id);

CREATE INDEX IF NOT EXISTS idx_model_usage_runs_user_created
ON model_usage_runs(user_id, created_at);

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
    owner_user_id INTEGER,
    source_kind TEXT NOT NULL DEFAULT 'system'
        CHECK (source_kind IN ('system', 'user')),
    tool_type TEXT NOT NULL DEFAULT 'python_builtin'
        CHECK (tool_type IN ('python_builtin', 'executable', 'system_command')),
    platform TEXT NOT NULL DEFAULT 'all'
        CHECK (platform IN ('windows', 'linux', 'all')),
    executable_path TEXT NOT NULL DEFAULT '',
    working_dir TEXT NOT NULL DEFAULT '',
    argv_template_json TEXT NOT NULL DEFAULT '[]',
    input_schema_json TEXT NOT NULL DEFAULT '{}',
    allowed_roots_json TEXT NOT NULL DEFAULT '["*"]',
    storage_path TEXT NOT NULL DEFAULT '',
    entrypoint TEXT NOT NULL DEFAULT '',
    code_sha256 TEXT NOT NULL DEFAULT '',
    validation_status TEXT NOT NULL DEFAULT 'valid'
        CHECK (validation_status IN ('pending', 'valid', 'invalid')),
    validation_error TEXT NOT NULL DEFAULT '',
    deleted_at TEXT,
    is_enabled INTEGER NOT NULL DEFAULT 1
        CHECK (is_enabled IN (0, 1)),
    requires_confirmation INTEGER NOT NULL DEFAULT 0
        CHECK (requires_confirmation IN (0, 1)),
    risk_level TEXT NOT NULL DEFAULT 'low'
        CHECK (risk_level IN ('low', 'medium', 'high')),
    timeout_seconds INTEGER NOT NULL DEFAULT 30,
    max_output_bytes INTEGER NOT NULL DEFAULT 65536,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
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
    message_id INTEGER,
    tool_id INTEGER NOT NULL,
    step_index INTEGER NOT NULL DEFAULT 0,
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
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (tool_id) REFERENCES agent_tools(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_tool_runs_user_id
ON agent_tool_runs(user_id);

CREATE INDEX IF NOT EXISTS idx_agent_tool_runs_conversation_id
ON agent_tool_runs(conversation_id);
