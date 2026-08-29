"""PostgreSQL database access layer for The Webcraft Labs."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.environ.get("DATABASE_URL")

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "schema.sql"
)


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def db_cursor(commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur

        if commit:
            conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def init_db():
    """Create PostgreSQL tables if they do not already exist."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(schema)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _convert_params(sql, params):
    """Keep existing SQLite-style ? placeholders working with PostgreSQL."""
    if "?" in sql:
        sql = sql.replace("?", "%s")
    return sql, params


def query_all(sql, params=()):
    sql, params = _convert_params(sql, params)

    with db_cursor() as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def query_one(sql, params=()):
    sql, params = _convert_params(sql, params)

    with db_cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute(sql, params=()):
    """Execute INSERT/UPDATE/DELETE statements."""

    sql, params = _convert_params(sql, params)

    with db_cursor(commit=True) as cur:
        cur.execute(sql, params)

        if sql.strip().upper().startswith("INSERT"):
            try:
                row = cur.fetchone()
                if row:
                    return next(iter(dict(row).values()))
            except Exception:
                pass

        return None