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
    def now_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                SELECT id,model_type, model_name,logo_path FROM models
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
                    SELECT id AS model_id,logo_path,provider_type
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
    def update_conversation_title(self,conversationid:int,title:str):
        with self.lock:
            now = self.now_time()
            conn = self.get_db_connection()
            try:
                # 1. 当前用户的所有模型先取消激活
                conn.execute(
                    """
                    UPDATE conversations
                    SET title = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (title,now,conversationid)
                )
                conn.commit()
                return {
                    "code":200
                }
            except Exception as exc:
                 conn.rollback()
                 print(f"数据库操作错误: {exc}")
                 return {
                    "code":500
                }
    def get_tokens_count(self,conversation_id:int, date: str):
        with self.lock:
            #date(created_at) = '2026-07-30-9'：只查这一天
            #strftime('%H:00', created_at)：把时间归到小时
            #SUM(tokens_used)：统计这个小时内所有消息 token 总量
            #GROUP BY strftime('%H', created_at)：按小时分组
            conn = self.get_db_connection()
            try:
                parts = date.rsplit("-", 1)
                if len(parts) != 2:
                    return {
                        "code": 400,
                        "message": "日期格式错误，应为 YYYY-MM-DD-H，例如 2026-07-30-9"
                }
                day = parts[0]      # 2026-07-30
                hour_text = parts[1]  # 9
                end_hour = int(hour_text)
                if end_hour < 0 or end_hour > 23:
                    return {
                        "code": 400,
                        "message": "小时范围错误，应为 0~23"
                    }
                rows = conn.execute(
                """
                SELECT 
                    CAST(strftime('%H', created_at) AS INTEGER) AS hour,
                    SUM(tokens_used) AS tokens
                FROM messages
                WHERE conversation_id = ?
                  AND date(created_at) = ?
                  AND CAST(strftime('%H', created_at) AS INTEGER) <= ?
                GROUP BY CAST(strftime('%H', created_at) AS INTEGER)
                ORDER BY hour
                """,
                (conversation_id, day, end_hour)
                ).fetchall()
                total_row = conn.execute(
                    """
                    SELECT 
                        COALESCE(SUM(tokens_used), 0) AS total_tokens
                    FROM messages
                    WHERE conversation_id = ?
                    AND date(created_at) = ?
                    AND CAST(strftime('%H', created_at) AS INTEGER) <= ?
                    """,
                    (conversation_id, day, end_hour)
                ).fetchone()
                hourly_map = {
                    hour: 0
                    for hour in range(end_hour + 1)
                }
                for row in rows:
                    hourly_map[row["hour"]] = row["tokens"] or 0
                items = [
                    {
                        "time": f"{hour:02d}:00",
                        "tokens": tokens
                    }
                    for hour, tokens in hourly_map.items()
                ]
                return {
                    "date": day,
                    "end_hour": end_hour,
                    "total_tokens": total_row["total_tokens"] if total_row else 0,
                    "items": items
                }
            except ValueError:
                return {
                    "code": 400,
                    "message": "小时格式错误，应为数字，例如 2026-07-30-9"
                }
            except Exception as exc:
                print(f"数据库操作错误: {exc}")
                return {
                    "code": 500
                }
            

    def get_proxy_config_by_user_id(self,user_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                cache_config = cache_manager.get(("proxy_config", user_id))
                if cache_config is not None:
                    return cache_config
                row = conn.execute(
                    """
                    SELECT *
                    FROM proxy_configs
                    WHERE user_id = ?
                    """,
                    (user_id,)
                ).fetchone()
                if row is None:
                    return {}
                result = dict(row)
                cache_manager.set(("proxy_config", user_id),result)
                return result
            except Exception as exc:
                print(f"数据库操作错误: {exc}")
                return {
                    "code":500
                }   

    def create_proxy_config(self,user_id:int,proxy_host:str,proxy_port:int,is_active:int):
        with self.lock:
            now = self.now_time()
            conn = self.get_db_connection()
            try:
                existing = conn.execute(
                    """
                    SELECT id FROM proxy_configs 
                    WHERE user_id = ?
                    """,
                        (user_id,)
                    ).fetchone()
                if existing:
                    proxy_id = existing["id"]
                    conn.execute(
                            """
                            UPDATE proxy_configs 
                            SET proxy_host = ?, proxy_port = ?, is_active = ?, updated_at = ?
                            WHERE id = ?
                            """,
                            (proxy_host,proxy_port, is_active,now,proxy_id)
                        )
                else:
                    cursor = conn.execute(
                        """
                        INSERT INTO proxy_configs (user_id, proxy_host, proxy_port, is_active ,created_at,updated_at)
                        VALUES (?,?,?,?,?,?)
                        """,
                        (user_id, proxy_host,proxy_port,is_active,now,now)
                    )
                conn.commit()
                row = conn.execute(
                        """
                        SELECT *
                        FROM proxy_configs
                        WHERE user_id = ?
                        """,
                        (user_id,)
                    ).fetchone()
                if row is None:
                    return {}
                result = dict(row)
                cache_manager.set(("proxy_config", user_id),result)
                return result
            except Exception as exc:
                conn.rollback()
                print(f"数据库操作错误: {exc}")
                return {
                    "code":500
                }

    def create_model_config(self,user_id:int,model_type:str,model_name:str,
              api_key:str, is_online:int):
        with self.lock:
            now = self.now_time()
            conn = self.get_db_connection()
            try:
                # 1. 当前用户的所有模型先取消激活
                conn.execute(
                    """
                    UPDATE model_configs
                    SET is_active = 0,
                        updated_at = ?
                    WHERE user_id = ?
                    """,
                    (now,user_id,)
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
                    SET api_key = ?, is_online = ?, is_active = 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (api_key, is_online,now,config_id)
                     )
                else:
                    cursor = conn.execute(
                        """
                        INSERT INTO model_configs (user_id, model_type, model_name, api_key, is_online, is_active,created_at,updated_at)
                        VALUES (?,?,?,?,?,?,?,?)
                        """,
                        (user_id, model_type,model_name,api_key,
                        is_online,1,now,now)
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
                    SELECT id AS model_id,logo_path,provider_type
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
    def get_conversation_by_user_id(self,user_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT id,title
                    FROM conversations
                    WHERE user_id = ?
                    """,
                    (user_id,)
                ).fetchall()
                return [dict(row) for row in rows] if rows else []
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
    def get_recent_messages_for_context(self, conversation_id: int, limit: int = 20):
        with self.lock:
            conn = self.get_db_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT role, content
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (conversation_id, limit)
                ).fetchall()
                messages = [dict(row) for row in reversed(rows)] #这里倒叙查询要二次反转作为输入
                return messages
            except Exception as exc:
                print(f"数据库操作错误: {exc}")
                return {
                    "code": 500
                }
    def get_messages_page(self,conversation_id:int,limit: int , before_id:int):
        with self.lock:
            conn = self.get_db_connection()
            try:
                if(before_id == -1): 
                    before_id = None
                limit = max(1, min(limit, 100))
                rows = conn.execute(
                """
                SELECT *
                FROM messages
                WHERE conversation_id = ?
                  AND (? IS NULL OR id < ?)
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, before_id, before_id, limit + 1)
                ).fetchall()
                has_more = len(rows) > limit
                rows = rows[:limit]
                messages = [dict(row) for row in reversed(rows)]
                return {
                "messages": messages,
                "has_more": has_more,
                "next_before_id": messages[0]["id"] if messages else -1
                }
            except Exception as exc:
                conn.rollback()
                print(f"数据库操作错误: {exc}")
                return {
                    "code": 500
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
    def create_messages(self,model_id:int,conversation_id:int,role: str,content:str, tokens_used: int = 0):
        with self.lock:
            conn = self.get_db_connection()
            try:
                now = self.now_time()
                cursor = conn.execute(
                    """
                    INSERT INTO messages (model_id,conversation_id, role, content,tokens_used,created_at)
                    VALUES (?, ?,?, ?, ?, ?)
                    """,
                    (model_id,conversation_id, role, content, tokens_used,now)
                )
                conn.commit()
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
                now = self.now_time()
                cursor = conn.execute(
                    """
                    INSERT INTO conversations (user_id, model_config_id,title,created_at,updated_at)
                    VALUES (?, ?, ?,?,?)
                    """,
                    (user_id, model_config_id,title,now,now)
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
                now = self.now_time()
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash,created_at)
                    VALUES (?, ?,?)
                    """,
                    (username, password_hash,now)
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
