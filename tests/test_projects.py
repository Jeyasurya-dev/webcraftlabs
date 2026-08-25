import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.conftest_helper import make_test_app


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.client = self.app.test_client()
        self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "ChangeMe123!"},
        )

    def tearDown(self):
        path = self.app.config.get("_TEST_DB_PATH")
        if path and os.path.exists(path):
            os.remove(path)

    def create_project(self, published=True, featured=False, title="Acme Storefront"):
        data = {
            "title": title,
            "category": "E-Commerce",
            "description": "A modern online store.",
            "technology": "Flask, SQLite",
            "live_url": "https://acme.example.com",
        }
        if published:
            data["is_published"] = "on"
        if featured:
            data["is_featured"] = "on"
        self.client.post("/admin/projects/new", data=data)
        from database.database import query_one
        return query_one("SELECT * FROM projects WHERE title = ?", (title,))

    def test_unpublished_project_hidden_from_public(self):
        self.create_project(published=False)
        r = self.client.get("/portfolio")
        self.assertNotIn(b"Acme Storefront", r.data)

    def test_published_project_visible_on_public_portfolio(self):
        self.create_project(published=True)
        r = self.client.get("/portfolio")
        self.assertIn(b"Acme Storefront", r.data)

    def test_empty_portfolio_shows_empty_state(self):
        r = self.client.get("/portfolio")
        self.assertIn(b"case study is in progress", r.data)

    def test_featured_project_appears_on_homepage(self):
        self.create_project(published=True, featured=True)
        r = self.client.get("/")
        self.assertIn(b"Acme Storefront", r.data)

    def test_edit_project_updates_title(self):
        project = self.create_project()
        self.client.post(
            f"/admin/projects/{project['id']}/edit",
            data={"title": "Acme Storefront v2", "category": "E-Commerce", "is_published": "on"},
        )
        r = self.client.get("/portfolio")
        self.assertIn(b"Acme Storefront v2", r.data)

    def test_unpublish_hides_from_portfolio(self):
        project = self.create_project(published=True)
        self.client.post(f"/admin/projects/{project['id']}/toggle-publish")
        r = self.client.get("/portfolio")
        self.assertNotIn(b"Acme Storefront", r.data)

    def test_delete_project_removes_it(self):
        project = self.create_project()
        self.client.post(f"/admin/projects/{project['id']}/delete")
        from database.database import query_all
        rows = query_all("SELECT * FROM projects WHERE id = ?", (project["id"],))
        self.assertEqual(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
