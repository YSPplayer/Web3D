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
        REFERENCES conversations(id) ON DELETE CASCADE
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
)