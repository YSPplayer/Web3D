import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from Config.config import config
from System.log_manager import get_logger


logger = get_logger(__name__)


class AuthTokenError(Exception):
    """Access Token 无效、过期或用途不正确。"""


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: int
    session_id: str


class AuthManager:
    def __init__(self):
        configured_secret = os.getenv("CHATAI_JWT_SECRET", "").strip()
        if configured_secret:
            self._secret = configured_secret
        else:
            self._secret = secrets.token_urlsafe(64)
            logger.warning(
                "未配置 CHATAI_JWT_SECRET，当前进程将使用临时密钥；"
                "生产环境或多进程部署必须配置固定密钥"
            )
        self._algorithm = "HS256"
        self._issuer = "chatai-server"
        self._audience = "chatai-web"

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def to_db_time(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def create_access_token(self, user_id: int, session_id: str) -> str:
        now = self.utc_now()
        expires_at = now + timedelta(minutes=config.auth_access_token_minutes)
        return jwt.encode(
            {
                "sub": str(user_id),
                "sid": session_id,
                "type": "access",
                "iss": self._issuer,
                "aud": self._audience,
                "iat": now,
                "exp": expires_at,
            },
            self._secret,
            algorithm=self._algorithm,
        )

    def decode_access_token(
        self,
        token: str,
        verify_expiration: bool = True,
    ) -> AccessTokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                options={
                    "require": ["sub", "sid", "type", "iat", "exp"],
                    "verify_exp": verify_expiration,
                },
            )
            if payload.get("type") != "access":
                raise AuthTokenError("Token 类型不正确")
            user_id = int(payload["sub"])
            session_id = str(payload["sid"]).strip()
            if user_id <= 0 or not session_id:
                raise AuthTokenError("Token 身份无效")
            return AccessTokenClaims(user_id=user_id, session_id=session_id)
        except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise AuthTokenError("Access Token 无效或已过期") from exc

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def refresh_expires_at(self) -> str:
        expires_at = self.utc_now() + timedelta(days=config.auth_refresh_token_days)
        return self.to_db_time(expires_at)

    def utc_now_string(self) -> str:
        return self.to_db_time(self.utc_now())


auth_manager = AuthManager()
