import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from Data.db_manager import db_manager
from Model.key import key
from Server.server import REFRESH_COOKIE_NAME, app


class AuthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.original_db_path = db_manager.db_path
        db_manager.close_db()
        self.db_path = Path(__file__).resolve().parent / ".test_auth_api.db"
        self.db_path.unlink(missing_ok=True)
        db_manager.db_path = self.db_path
        db_manager.init_db()
        created = db_manager.create_user(
            "api-auth-user",
            key.string_to_bcrypt_hash("client-password-digest"),
        )
        self.user_id = created["id"]
        other_user = db_manager.create_user(
            "other-api-user",
            key.string_to_bcrypt_hash("other-password-digest"),
        )
        self.other_user_id = other_user["id"]
        conn = db_manager.get_db_connection()
        now = "2026-01-01 00:00:00"
        cursor = conn.execute(
            """
            INSERT INTO model_configs (
                user_id, model_type, model_name, api_key,
                is_online, is_active, created_at, updated_at
            ) VALUES (?, 'glm', 'glm-4-flash', 'encrypted', 1, 1, ?, ?)
            """,
            (self.other_user_id, now, now),
        )
        self.other_model_config_id = cursor.lastrowid
        cursor = conn.execute(
            """
            INSERT INTO conversations (
                user_id, model_config_id, title, created_at, updated_at
            ) VALUES (?, ?, 'private', ?, ?)
            """,
            (self.other_user_id, self.other_model_config_id, now, now),
        )
        self.other_conversation_id = cursor.lastrowid
        conn.commit()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        db_manager.close_db()
        self.db_path.unlink(missing_ok=True)
        db_manager.db_path = self.original_db_path

    def test_login_refresh_rotation_and_authenticated_user_boundary(self):
        unauthenticated = self.client.get(
            "/chatai/user/getConversationByUserId",
            params={"userid": self.user_id},
        )
        self.assertEqual(unauthenticated.status_code, 401)

        wrong_password = self.client.post(
            "/chatai/login",
            json={
                "username": "api-auth-user",
                "password": "wrong-digest",
            },
        )
        self.assertEqual(wrong_password.status_code, 401)

        login = self.client.post(
            "/chatai/login",
            json={
                "username": "api-auth-user",
                "password": "client-password-digest",
            },
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("HttpOnly", login.headers["set-cookie"])
        self.assertIn("SameSite=lax", login.headers["set-cookie"])
        self.assertEqual(login.headers["cache-control"], "no-store")
        login_data = login.json()["data"]
        access_token = login_data["access_token"]
        old_refresh_token = login.cookies.get(REFRESH_COOKIE_NAME)
        self.assertNotIn(old_refresh_token, login.text)
        stored_refresh_hash = db_manager.get_db_connection().execute(
            "SELECT refresh_token_hash FROM auth_sessions WHERE user_id = ?",
            (self.user_id,),
        ).fetchone()["refresh_token_hash"]
        self.assertNotEqual(stored_refresh_hash, old_refresh_token)

        authorized = self.client.get(
            "/chatai/user/getConversationByUserId",
            params={"userid": self.user_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(authorized.status_code, 200)

        forged_user = self.client.get(
            "/chatai/user/getConversationByUserId",
            params={"userid": self.user_id + 1},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(forged_user.status_code, 403)

        foreign_conversation = self.client.get(
            "/chatai/user/chatPageMessages",
            params={
                "conversationid": self.other_conversation_id,
                "limit": 20,
                "beforeid": -1,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(foreign_conversation.status_code, 404)

        foreign_model_config = self.client.post(
            "/chatai/user/conversation",
            json={
                "userid": self.user_id,
                "modelconfigid": self.other_model_config_id,
                "title": "forbidden",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(foreign_model_config.status_code, 404)

        refreshed = self.client.post("/chatai/auth/refresh")
        self.assertEqual(refreshed.status_code, 200)
        refreshed_access_token = refreshed.json()["data"]["access_token"]
        self.assertNotEqual(
            old_refresh_token,
            refreshed.cookies.get(REFRESH_COOKIE_NAME),
        )

        replay_client = TestClient(app)
        replay_client.cookies.set(REFRESH_COOKIE_NAME, old_refresh_token)
        replay = replay_client.post("/chatai/auth/refresh")
        replay_client.close()
        self.assertEqual(replay.status_code, 401)

        logout = self.client.post(
            "/chatai/auth/logout",
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )
        self.assertEqual(logout.status_code, 200)
        after_logout = self.client.post("/chatai/auth/refresh")
        self.assertEqual(after_logout.status_code, 401)
        old_access_after_logout = self.client.get(
            "/chatai/user/getConversationByUserId",
            params={"userid": self.user_id},
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )
        self.assertEqual(old_access_after_logout.status_code, 401)

    def test_credentialed_cors_uses_explicit_frontend_origin(self):
        response = self.client.options(
            "/chatai/auth/refresh",
            headers={
                "Origin": "http://localhost:5729",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5729",
        )
        self.assertEqual(
            response.headers["access-control-allow-credentials"], "true"
        )


if __name__ == "__main__":
    unittest.main()
