import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "webcraft.db")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@thewebcraftlabs.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
    UPLOAD_MAX_MB = int(os.environ.get("UPLOAD_MAX_MB", 5))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB hard cap on any request body


class TestConfig(Config):
    TESTING = True
    DATABASE_URL = ":memory:"
    WTF_CSRF_ENABLED = False
