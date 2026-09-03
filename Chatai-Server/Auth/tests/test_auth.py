import unittest
from datetime import timedelta
from pathlib import Path

from Auth import AuthTokenError, auth_manager
from Config.config import config
from Data.db_manager import DBManager


class AccessTokenTests(unittest.TestCase):
    def test_access_token_round_trip_and_tamper_rejection(self):
        token = auth_manager.create_access_token(7, "session-1")
        claims = auth_manager.decode_access_token(token)

        self.assertEqual(claims.user_id, 7)
        self.assertEqual(claims.session_id, "session-1")
        with self.assertRaises(AuthTokenError):
            auth_manager.decode_access_token(f"{token}x")

    def test_refresh_token_is_stored_as_hash(self):
        token = auth_manager.create_refresh_token()
        token_hash = auth_manager.hash_refresh_token(token)

        self.assertNotEqual(token, token_hash)
        self.assertEqual(len(token_hash), 64)

    def test_expired_access_token_is_rejected(self):
        original_minutes = config.auth_access_token_minutes
        try:
            config.auth_access_token_minutes = -1
            token = auth_manager.create_access_token(7, "session-1")
        finally:
            config.auth_access_token_minutes = original_minutes

        with self.assertRaises(AuthTokenError):
            auth_manager.decode_access_token(token)


class RefreshSessionRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.db_path = Path(__file__).resolve().parent / ".test_auth_session.db"
        self.db_path.unlink(missing_ok=True)
        self.manager = DBManager()
        self.manager.db_path = self.db_path
        self.manager.init_db()
        conn = self.manager.get_db_connection()
        conn.execute(
            """
            INSERT INTO users (
                username, password_hash, avatar_base64, avatar_mime,
                created_at, updated_at
            ) VALUES (?, ?, '', 'image/png', ?, ?)
            """,
            ("auth-user", "hash", "2026-01-01 00:00:00", "2026-01-01 00:00:00"),
        )
        conn.commit()
        self.user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("auth-user",)
        ).fetchone()["id"]

    def tearDown(self):
        self.manager.close_db()
        self.db_path.unlink(missing_ok=True)

    def test_refresh_rotation_invalidates_old_token_and_logout_revokes_new_token(self):
        old_token = auth_manager.create_refresh_token()
        new_token = auth_manager.create_refresh_token()
        now = auth_manager.utc_now_string()
        expires_at = auth_manager.to_db_time(
            auth_manager.utc_now() + timedelta(days=1)
        )
        created = self.manager.create_auth_session(
            "session-1",
            self.user_id,
            auth_manager.hash_refresh_token(old_token),
            expires_at,
            now,
        )
        self.assertEqual(created["id"], "session-1")

        rotated = self.manager.rotate_auth_session(
            auth_manager.hash_refresh_token(old_token),
            auth_manager.hash_refresh_token(new_token),
            now,
        )
        self.assertEqual(rotated["user_id"], self.user_id)

        old_result = self.manager.rotate_auth_session(
            auth_manager.hash_refresh_token(old_token),
            auth_manager.hash_refresh_token(auth_manager.create_refresh_token()),
            now,
        )
        self.assertEqual(old_result["code"], 401)

        revoked = self.manager.revoke_auth_session(
            auth_manager.hash_refresh_token(new_token), now
        )
        self.assertEqual(revoked["code"], 200)
        revoked_result = self.manager.rotate_auth_session(
            auth_manager.hash_refresh_token(new_token),
            auth_manager.hash_refresh_token(auth_manager.create_refresh_token()),
            now,
        )
        self.assertEqual(revoked_result["code"], 401)


if __name__ == "__main__":
    unittest.main()
