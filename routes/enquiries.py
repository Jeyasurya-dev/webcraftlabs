"""
Business logic for project enquiries (the contact form). Kept separate
from the public route handler so validation/persistence can be unit
tested and reused (e.g. from the admin panel) independently of Flask
request objects.
"""

import re

from database.database import execute, query_all, query_one


SERVICE_OPTIONS = [
    "Business Website",
    "Portfolio Website",
    "E-Commerce Website",
    "AI-Powered Website",
    "Custom Web Application",
    "Other",
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__("Validation failed")


def _clean(value):
    return (value or "").strip()


def validate_enquiry(form: dict) -> dict:
    name = _clean(form.get("name"))
    email = _clean(form.get("email"))
    phone = _clean(form.get("phone"))
    company = _clean(form.get("company"))
    service = _clean(form.get("service"))
    budget_range = _clean(form.get("budget_range"))
    message = _clean(form.get("message"))

    errors = {}

    if len(name) < 2:
        errors["name"] = "Please enter your full name."

    if not EMAIL_RE.match(email):
        errors["email"] = "Please enter a valid email address."

    if service not in SERVICE_OPTIONS:
        errors["service"] = "Please choose a service."

    if len(message) < 10:
        errors["message"] = (
            "Please tell us a bit more about your project "
            "(10+ characters)."
        )

    if errors:
        raise ValidationError(errors)

    return {
        "name": name[:200],
        "email": email[:200],
        "phone": phone[:50],
        "company": company[:200],
        "service": service,
        "budget_range": budget_range[:100],
        "message": message[:5000],
    }


def create_enquiry(form: dict) -> int:
    data = validate_enquiry(form)

    return execute(
        """INSERT INTO enquiries
           (name, email, phone, company, service, budget_range, message)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            data["name"],
            data["email"],
            data["phone"],
            data["company"],
            data["service"],
            data["budget_range"],
            data["message"],
        ),
    )


def list_enquiries(status: str = None):
    if status:
        return query_all(
            "SELECT * FROM enquiries "
            "WHERE status = ? "
            "ORDER BY created_at DESC",
            (status,),
        )

    return query_all(
        "SELECT * FROM enquiries ORDER BY created_at DESC"
    )


def get_enquiry(enquiry_id: int):
    return query_one(
        "SELECT * FROM enquiries WHERE id = ?",
        (enquiry_id,),
    )


def update_enquiry_status(enquiry_id: int, status: str):
    execute(
        "UPDATE enquiries "
        "SET status = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (status, enquiry_id),
    )


def delete_enquiry(enquiry_id: int):
    execute(
        "DELETE FROM enquiries WHERE id = ?",
        (enquiry_id,),
    )