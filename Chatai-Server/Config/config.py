from pathlib import Path
class Config:
    def __init__(self):
        self.main_path = Path(__file__).resolve().parent.parent
        self.db_path = self.main_path / "Data"
        self.log_path = self.main_path / "Logs"
        self.sql_path = self.main_path / "Sql"
        self.server_ip = "127.0.0.1"
        self.server_port = 8231

config = Config()