import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_test_app():
    """Creates a Flask app wired to a throwaway file-based SQLite DB."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.remove(db_path)
    os.environ["DATABASE_URL"] = db_path
    os.environ["ADMIN_EMAIL"] = "admin@thewebcraftlabs.com"
    os.environ["ADMIN_PASSWORD"] = "ChangeMe123!"

    # Re-import fresh so database.database picks up the new DATABASE_URL
    import importlib
    import database.database as dbmod
    importlib.reload(dbmod)

    from app import create_app, ensure_bootstrapped
    from config import Config

    class TestConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = False

    app = create_app(TestConfig)
    ensure_bootstrapped(app)
    app.config["_TEST_DB_PATH"] = db_path
    return app
