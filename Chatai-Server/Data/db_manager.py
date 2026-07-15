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
    def get_user_by_username(self, username: str):
        with self.lock:
            conn = self.get_db_connection()

            row = conn.execute(
                """
                SELECT id, username, password_hash, created_at
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

            return dict(row) if row else None
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
            except Exception:
                conn.rollback()
                raise

db_manager = DBManager()