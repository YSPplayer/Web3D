import os
from pathlib import Path
class Config:
    def __init__(self):
        self.main_path = Path(__file__).resolve().parent.parent
        self.db_path = self.main_path / "Data"
        self.log_path = self.main_path / "Logs"
        self.sql_path = self.main_path / "Sql"
        self.local_model_path = self.db_path / "model"
        self.server_ip = "127.0.0.1"
        self.server_port = 8231
        self.auth_access_token_minutes = max(
            1, int(os.getenv("CHATAI_ACCESS_TOKEN_MINUTES", "15"))
        )
        self.auth_refresh_token_days = max(
            1, int(os.getenv("CHATAI_REFRESH_TOKEN_DAYS", "7"))
        )
        self.auth_cookie_secure = os.getenv(
            "CHATAI_COOKIE_SECURE", "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        origins = os.getenv(
            "CHATAI_ALLOWED_ORIGINS",
            "http://localhost:5729",
        )
        self.allowed_origins = [
            origin.strip() for origin in origins.split(",") if origin.strip()
        ]

config = Config()
