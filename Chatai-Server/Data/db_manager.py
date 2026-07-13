import sqlite3
import os
from Config.config import config
class DBManager:
    def __init__(self):
        self.db_path = config.db_path.join("chat_data.db")
        self.conn = None
    def get_db_connection(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 让查询结果可以按列名访问
        return self.conn
    def init_db(self):
        sql_path = config.sql_path.join("run.sql")
        if not os.path.exists(sql_path):
            raise FileNotFoundError(f"SQL文件不存在: {sql_path}")
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        """初始化数据库：创建所有表"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        print(f"✅ 数据库初始化成功！从 {sql_path} 加载")
    