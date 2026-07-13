import os
class Config:
    def __init__(self):
        # 获取当前文件所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 定义各个路径
        self.main_path = base_dir
        self.db_path = os.path.join(base_dir, "Data")
        self.log_path = os.path.join(base_dir, "Logs")
        self.sql_path = os.path.join(base_dir, "Sql")

config = Config()