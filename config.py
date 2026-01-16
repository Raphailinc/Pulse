import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR/'social.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_ROOT = BASE_DIR / "static" / "uploads"
    UPLOAD_FOLDER = UPLOAD_ROOT
    PROFILE_UPLOAD_FOLDER = UPLOAD_ROOT / "profiles"
    POST_UPLOAD_FOLDER = UPLOAD_ROOT / "posts"

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP", "GIF"}


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = os.environ.get("TEST_SECRET_KEY", secrets.token_hex(16))
    UPLOAD_ROOT = Config.UPLOAD_ROOT / "test"
    PROFILE_UPLOAD_FOLDER = UPLOAD_ROOT / "profiles"
    POST_UPLOAD_FOLDER = UPLOAD_ROOT / "posts"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
