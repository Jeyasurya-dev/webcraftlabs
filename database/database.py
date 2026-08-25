"""
Database access layer.

Everything goes through parameterized queries — never string-concatenated
SQL. The schema and access pattern here (explicit columns, no SQLite-only
functions besides datetime('now')) are chosen so a future move to
PostgreSQL only requires swapping the connection/driver, not rewriting
call sites.
"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get(
    "DATABASE_URL",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webcraft.db"),
)
if DB_PATH.startswith("sqlite:///"):
    DB_PATH = DB_PATH.replace("sqlite:///", "", 1)

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor(commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not already exist."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def query_all(sql, params=()):
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def query_one(sql, params=()):
    with db_cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute(sql, params=()):
    """For INSERT/UPDATE/DELETE. Returns lastrowid."""
    with db_cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.lastrowid
