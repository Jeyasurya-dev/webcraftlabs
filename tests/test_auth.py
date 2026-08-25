import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.conftest_helper import make_test_app


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.client = self.app.test_client()

    def tearDown(self):
        path = self.app.config.get("_TEST_DB_PATH")
        if path and os.path.exists(path):
            os.remove(path)

    def test_protected_route_redirects_when_logged_out(self):
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login", r.headers["Location"])

    def test_wrong_password_rejected(self):
        r = self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "wrong-password"},
        )
        self.assertEqual(r.status_code, 401)

    def test_correct_login_grants_access(self):
        r = self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "ChangeMe123!"},
            follow_redirects=True,
        )
        self.assertEqual(r.status_code, 200)
        r2 = self.client.get("/admin/")
        self.assertEqual(r2.status_code, 200)

    def test_logout_revokes_access(self):
        self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "ChangeMe123!"},
        )
        self.client.post("/admin/logout")
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 302)

    def test_passwords_are_hashed_not_plaintext(self):
        from services.auth import get_admin_by_email
        admin = get_admin_by_email("admin@thewebcraftlabs.com")
        self.assertNotEqual(admin["password_hash"], "ChangeMe123!")
        self.assertTrue(admin["password_hash"].startswith(("pbkdf2:", "scrypt:")))


if __name__ == "__main__":
    unittest.main()
