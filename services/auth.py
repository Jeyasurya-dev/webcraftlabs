"""
Admin authentication: password hashing, session helpers, route protection.
"""
from functools import wraps
from flask import session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database.database import query_one, execute


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def get_admin_by_email(email: str):
    return query_one("SELECT * FROM admins WHERE email = ?", (email,))


def create_admin(email: str, password: str, name: str = "Admin"):
    return execute(
        "INSERT INTO admins (email, password_hash, name) VALUES (?, ?, ?)",
        (email, hash_password(password), name),
    )


def authenticate(email: str, password: str):
    admin = get_admin_by_email(email)
    if admin and verify_password(password, admin["password_hash"]):
        execute("UPDATE admins SET last_login_at = datetime('now') WHERE id = ?", (admin["id"],))
        return admin
    return None


def current_admin():
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    return query_one("SELECT id, email, name FROM admins WHERE id = ?", (admin_id,))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
