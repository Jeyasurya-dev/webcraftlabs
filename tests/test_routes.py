import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.conftest_helper import make_test_app


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.client = self.app.test_client()

    def tearDown(self):
        path = self.app.config.get("_TEST_DB_PATH")
        if path and os.path.exists(path):
            os.remove(path)

    def test_all_public_pages_load(self):
        for path in ["/", "/services", "/portfolio", "/about", "/careers", "/contact",
                     "/robots.txt", "/sitemap.xml", "/favicon.ico"]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200, f"{path} failed with {r.status_code}")

    def test_404_for_unknown_route(self):
        r = self.client.get("/this-route-does-not-exist")
        self.assertEqual(r.status_code, 404)

    def test_404_for_unknown_job_slug(self):
        r = self.client.get("/careers/does-not-exist")
        self.assertEqual(r.status_code, 404)

    def test_all_admin_routes_require_auth(self):
        protected = [
            "/admin/", "/admin/enquiries", "/admin/projects", "/admin/projects/new",
            "/admin/careers", "/admin/careers/new", "/admin/applications", "/admin/settings",
        ]
        for path in protected:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 302, f"{path} was not protected")
            self.assertIn("/admin/login", r.headers["Location"])

    def test_admin_pages_load_once_authenticated(self):
        self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "ChangeMe123!"},
        )
        for path in ["/admin/", "/admin/enquiries", "/admin/projects", "/admin/projects/new",
                     "/admin/careers", "/admin/careers/new", "/admin/applications", "/admin/settings"]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200, f"{path} failed with {r.status_code}")


if __name__ == "__main__":
    unittest.main()
