import io
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.conftest_helper import make_test_app


class CareersTests(unittest.TestCase):
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

    def create_job(self, status="Draft", title="Backend Engineer"):
        self.client.post(
            "/admin/careers/new",
            data={
                "title": title,
                "department": "Engineering",
                "employment_type": "Full-time",
                "location": "Remote",
                "description": "Build and maintain our backend services.",
                "responsibilities": "Write code\nReview PRs",
                "requirements": "3+ years Python",
                "status": status,
            },
        )
        from database.database import query_one
        return query_one("SELECT * FROM jobs WHERE title = ?", (title,))

    def test_draft_job_not_public(self):
        self.create_job(status="Draft")
        r = self.client.get("/careers")
        self.assertNotIn(b"Backend Engineer", r.data)

    def test_open_job_is_public(self):
        self.create_job(status="Open")
        r = self.client.get("/careers")
        self.assertIn(b"Backend Engineer", r.data)

    def test_job_detail_page_loads(self):
        job = self.create_job(status="Open")
        r = self.client.get(f"/careers/{job['slug']}")
        self.assertEqual(r.status_code, 200)

    def test_application_submission_and_admin_visibility(self):
        job = self.create_job(status="Open")
        resume = (io.BytesIO(b"%PDF-1.4 fake content"), "resume.pdf")
        r = self.client.post(
            f"/careers/{job['slug']}",
            data={
                "full_name": "John Applicant",
                "email": "john@example.com",
                "phone": "12345",
                "portfolio_url": "https://johndoe.dev",
                "cover_message": "I would love to join the team.",
                "resume": resume,
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(r.status_code, 200)

        r2 = self.client.get("/admin/applications")
        self.assertIn(b"John Applicant", r2.data)

    def test_resume_rejected_for_wrong_extension(self):
        job = self.create_job(status="Open")
        bad_file = (io.BytesIO(b"not a resume"), "resume.exe")
        r = self.client.post(
            f"/careers/{job['slug']}",
            data={"full_name": "Bad Actor", "email": "bad@example.com", "resume": bad_file},
            content_type="multipart/form-data",
        )
        self.assertEqual(r.status_code, 400)

    def test_closed_job_rejects_applications(self):
        job = self.create_job(status="Open")
        from database.database import execute
        execute("UPDATE jobs SET status = 'Closed' WHERE id = ?", (job["id"],))
        resume = (io.BytesIO(b"%PDF-1.4 fake"), "resume.pdf")
        r = self.client.post(
            f"/careers/{job['slug']}",
            data={"full_name": "Late Applicant", "email": "late@example.com", "resume": resume},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertIn(b"no longer accepting", r.data)

    def test_resume_not_accessible_without_auth(self):
        job = self.create_job(status="Open")
        resume = (io.BytesIO(b"%PDF-1.4 fake"), "resume.pdf")
        self.client.post(
            f"/careers/{job['slug']}",
            data={"full_name": "John Applicant", "email": "john@example.com", "resume": resume},
            content_type="multipart/form-data",
        )
        from database.database import query_one
        app_row = query_one("SELECT id FROM applications LIMIT 1")

        anon_client = self.app.test_client()
        r = anon_client.get(f"/admin/applications/{app_row['id']}/resume")
        self.assertEqual(r.status_code, 302)  # redirected to login, not served

    def test_job_status_workflow(self):
        job = self.create_job(status="Draft")
        self.client.post(f"/admin/careers/{job['id']}/status", data={"status": "Open"})
        r = self.client.get("/careers")
        self.assertIn(b"Backend Engineer", r.data)
        self.client.post(f"/admin/careers/{job['id']}/status", data={"status": "Closed"})
        r2 = self.client.get("/careers")
        self.assertNotIn(b"Backend Engineer", r2.data)


if __name__ == "__main__":
    unittest.main()
