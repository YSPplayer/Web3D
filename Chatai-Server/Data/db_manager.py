import sqlite3
import os
import threading
from contextlib import contextmanager
from Config.config import config
class DBManager:
    def __init__(self):
        self.db_path = config.db_path / "chat_data.db"
        self.conn = None
        self.lock = threading.RLock()

    def get_db_connection(self):
        """获取数据库连接"""
        with self.lock:
            if self.conn is None:
                self.conn = sqlite3.connect(
                    self.db_path,
                    timeout=10,
                    check_same_thread=False
                )
                self.conn.row_factory = sqlite3.Row
                self.conn.execute("PRAGMA foreign_keys = ON")
            return self.conn
    
    def close_db(self):
        with self.lock:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
                print("数据库连接已关闭")

    def init_db(self):
        sql_path = config.sql_path / "run.sql"
        if not os.path.exists(sql_path):
            raise FileNotFoundError(f"SQL文件不存在: {sql_path}")
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        """初始化数据库：创建所有表"""
        with self.lock:
            conn = self.get_db_connection()
            try:
                conn.executescript(sql_script)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        print(f"数据库初始化成功，从 {sql_path} 加载")
    def get_models(self):
        with self.lock:
            try:
                conn = self.get_db_connection()
                rows = conn.execute(
                """
                SELECT model_type, model_name,logo_path FROM models
                """).fetchall()
                return [dict(row) for row in rows] if rows else []
            except Exception:
                 return {
                    "code":505
                }

    def get_user_by_username(self, username: str):
        with self.lock:
            try:
                conn = self.get_db_connection()

                row = conn.execute(
                    """
                    SELECT id, username, password_hash, created_at
                    FROM users
                    WHERE username = ?
                    """,
                    (username,)
                ).fetchone()
                return dict(row) if row else {"code":401}
            except Exception:
                 return {
                    "code":505
                }
    def create_model_config(self,user_id:int,model_type:str,model_name:str,
              api_key:str, is_online:int, is_active:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                existing = conn.execute(
                """
                SELECT id FROM model_configs 
                WHERE user_id = ? AND model_type = ? AND model_name = ?
                """,
                    (user_id, model_type, model_name)
                ).fetchone()
                if existing:
                    # 2. 存在则更新
                    conn.execute(
                    """
                    UPDATE model_configs 
                    SET api_key = ?, is_online = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND model_type = ? AND model_name = ?
                    """,
                    (api_key, is_online, is_active, user_id, model_type, model_name)
                     )
                else:
                    cursor = conn.execute(
                        """
                        INSERT INTO model_configs (user_id, model_type, model_name, api_key, is_online, is_active)
                        VALUES (?,?,?,?,?,?)
                        """,
                        (user_id, model_type,model_name,api_key,
                        is_online,is_active)
                    )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT *
                    FROM model_configs
                    WHERE user_id = ?
                    """,
                    (user_id,)
                ).fetchone()
                return dict(row)
            except Exception:
                 return {
                    "code":505
                }
    def create_user(self,username:str, password_hash: str):
         with self.lock:
            conn = self.get_db_connection()
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                    """,
                    (username, password_hash)
                )
                user_id = cursor.lastrowid
                conn.commit()
                row = conn.execute(
                    """
                    SELECT id, username, created_at
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()
                return dict(row)
            except sqlite3.IntegrityError as exc:
                if "UNIQUE constraint failed: users.username" in str(exc):
                    return {
                        "code":409
                    }
                return {
                    "code":500
                }
            except Exception:
                 return {
                    "code":505
                }

db_manager = DBManager()