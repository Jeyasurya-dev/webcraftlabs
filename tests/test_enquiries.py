import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.conftest_helper import make_test_app


class EnquiryTests(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.client = self.app.test_client()

    def tearDown(self):
        path = self.app.config.get("_TEST_DB_PATH")
        if path and os.path.exists(path):
            os.remove(path)

    def valid_payload(self, **overrides):
        data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "9999999999",
            "company": "Acme Bakery",
            "service": "Business Website",
            "budget_range": "Not sure yet",
            "message": "We need a new website for our bakery business.",
        }
        data.update(overrides)
        return data

    def test_valid_enquiry_is_saved_and_visible_to_admin(self):
        r = self.client.post("/contact", data=self.valid_payload(), follow_redirects=True)
        self.assertEqual(r.status_code, 200)

        self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "ChangeMe123!"},
        )
        r2 = self.client.get("/admin/enquiries")
        self.assertIn(b"Jane Doe", r2.data)

    def test_invalid_email_rejected(self):
        r = self.client.post("/contact", data=self.valid_payload(email="not-an-email"))
        self.assertEqual(r.status_code, 400)

    def test_missing_name_rejected(self):
        r = self.client.post("/contact", data=self.valid_payload(name=""))
        self.assertEqual(r.status_code, 400)

    def test_invalid_service_rejected(self):
        r = self.client.post("/contact", data=self.valid_payload(service="Not A Real Service"))
        self.assertEqual(r.status_code, 400)

    def test_short_message_rejected(self):
        r = self.client.post("/contact", data=self.valid_payload(message="hi"))
        self.assertEqual(r.status_code, 400)

    def test_status_can_be_updated_by_admin(self):
        self.client.post("/contact", data=self.valid_payload())
        self.client.post(
            "/admin/login",
            data={"email": "admin@thewebcraftlabs.com", "password": "ChangeMe123!"},
        )
        from database.database import query_all
        enquiry_id = query_all("SELECT id FROM enquiries")[0]["id"]
        r = self.client.post(f"/admin/enquiries/{enquiry_id}", data={"status": "Contacted"}, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        row = query_all("SELECT status FROM enquiries WHERE id = ?", (enquiry_id,))[0]
        self.assertEqual(row["status"], "Contacted")

    def test_sql_injection_attempt_does_not_break_table(self):
        payload = self.valid_payload(name="Robert'); DROP TABLE enquiries;--")
        r = self.client.post("/contact", data=payload, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        from database.database import query_all
        rows = query_all("SELECT * FROM enquiries")
        self.assertEqual(len(rows), 1)
        self.assertIn("DROP TABLE", rows[0]["name"])


if __name__ == "__main__":
    unittest.main()
