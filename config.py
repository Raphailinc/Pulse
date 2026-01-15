import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR/'social.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_ROOT = BASE_DIR / "static" / "uploads"
    PROFILE_UPLOAD_FOLDER = UPLOAD_ROOT / "profiles"
    POST_UPLOAD_FOLDER = UPLOAD_ROOT / "posts"

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB per upload


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
