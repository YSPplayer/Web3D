import sqlite3
import os
import threading
from contextlib import contextmanager
from Config.config import config
from datetime import datetime
from Data.cache_manager import cache_manager
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
        cache_manager.clear()
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
            except Exception as exc:
                print(f"数据库操作错误: {exc}")
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
            except Exception as exc:
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
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
            except Exception as exc:
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
                }
    def get_model_config_state_by_user_par(self,user_id:int,
            model_type:str,model_name:str):
        with self.lock:
            conn = self.get_db_connection()
            try:
                row = conn.execute(
                    """
                    SELECT api_key,is_online
                    FROM model_configs
                    WHERE user_id = ? AND model_type = ? AND model_name = ? 
                    """,
                    (user_id,model_type, model_name)
                ).fetchone()
                imgs = conn.execute(
                    """
                    SELECT logo_path
                    FROM models
                    WHERE model_type = ? AND model_name = ? 
                    """,
                    (model_type, model_name)
                ).fetchone()
                if row is None:
                    return {}
                result = {**dict(row), **dict(imgs)} if imgs else dict(row)
                return result
            except Exception as exc:
                print(f"数据库操作错误: {exc}")
                return {
                    "code":500
                }   
    def get_model_config_by_userid(self,user_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                cache_config = cache_manager.get(("model_config", user_id))
                if cache_config is not None:
                    return cache_config
                row = conn.execute(
                    """
                    SELECT *
                    FROM model_configs
                    WHERE user_id = ? AND is_active = 1
                    """,
                    (user_id,)
                ).fetchone()
                if row is None:
                    return {}
                imgs = conn.execute(
                    """
                    SELECT logo_path,provider_type
                    FROM models
                    WHERE model_type = ? AND model_name = ? 
                    """,
                    (row["model_type"], row["model_name"])
                ).fetchone()
                result = {**dict(row), **dict(imgs)} if imgs else dict(row)
                cache_manager.set(("model_config", user_id),result)
                return result
            except Exception as exc:
                print(f"数据库操作错误: {exc}")
                return {
                    "code":500
                }   
    def create_model_config(self,user_id:int,model_type:str,model_name:str,
              api_key:str, is_online:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                # 1. 当前用户的所有模型先取消激活
                conn.execute(
                    """
                    UPDATE model_configs
                    SET is_active = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )
                existing = conn.execute(
                """
                SELECT id FROM model_configs 
                WHERE user_id = ? AND model_type = ? AND model_name = ?
                """,
                    (user_id, model_type, model_name)
                ).fetchone()
                if existing:
                    config_id = existing["id"]
                    # 2. 存在则更新
                    conn.execute(
                    """
                    UPDATE model_configs 
                    SET api_key = ?, is_online = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (api_key, is_online,config_id)
                     )
                else:
                    cursor = conn.execute(
                        """
                        INSERT INTO model_configs (user_id, model_type, model_name, api_key, is_online, is_active)
                        VALUES (?,?,?,?,?,?)
                        """,
                        (user_id, model_type,model_name,api_key,
                        is_online,1)
                    )
                conn.commit()
                row = conn.execute(
                    """
                    SELECT *
                    FROM model_configs
                    WHERE user_id = ? AND model_type = ? AND model_name = ?
                    """,
                    (user_id, model_type, model_name)
                ).fetchone()
                if row is None:
                    return {}
                imgs = conn.execute(
                    """
                    SELECT logo_path,provider_type
                    FROM models
                    WHERE model_type = ? AND model_name = ? 
                    """,
                    (row["model_type"], row["model_name"])
                ).fetchone()
                result = {**dict(row), **dict(imgs)} if imgs else dict(row)
                cache_manager.set(("model_config", user_id),result)
                return result
            except Exception as exc:
                 conn.rollback()
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
                }
    def delete_conversation(self,conversation_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                conn.execute(
                """
                DELETE FROM conversations
                WHERE id = ?
                """,
                (conversation_id,)
                )
                conn.commit()
                return {}
            except Exception as exc:
                conn.rollback()
                print(f"数据库操作错误: {exc}")
                return {
                    "code":500
                }

    def get_conversation(self,user_id:int,model_config_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT id,title
                    FROM conversations
                    WHERE user_id = ? AND model_config_id = ?
                    """,
                    (user_id, model_config_id)
                ).fetchall()
                return [dict(row) for row in rows] if rows else []
            except Exception as exc:
                 conn.rollback()
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
                }
    def get_messages(self,conversation_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT * FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY id ASC
                    """,
                    (conversation_id,)
                ).fetchall()
                return [dict(row) for row in rows] if rows else []
            except Exception as exc:
                 conn.rollback()
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
                }
    def create_messages(self,conversation_id:int,role: str,content:str, tokens_used: int = 0):
        with self.lock:
            conn = self.get_db_connection()
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content,tokens_used)
                    VALUES (?, ?,?, ?)
                    """,
                    (conversation_id, role, content, tokens_used)
                )
                conn.commit()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_id = cursor.lastrowid
                return {
                    "message_id" : new_id,
                    "created_at": now
                }
            except Exception as exc:
                conn.rollback()
                print(f"数据库操作错误: {exc}")
                return {
                    "code":500
                }

    def create_conversation(self,user_id:int,model_config_id:int,title:str):
        with self.lock:
            conn = self.get_db_connection()
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO conversations (user_id, model_config_id,title)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, model_config_id,title)
                )
                conn.commit()
                new_id = cursor.lastrowid
                return {
                    "conversation_id": new_id
                }
            except Exception as exc:
                 conn.rollback()
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
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
                conn.rollback()
                print(f"数据库操作错误: {exc}")
                if "UNIQUE constraint failed: users.username" in str(exc):
                    return {
                        "code":409
                    }
                return {
                    "code":500
                }
            except Exception as exc:
                 conn.rollback()
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
                }

db_manager = DBManager()
