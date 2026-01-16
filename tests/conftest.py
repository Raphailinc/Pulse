from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app import create_app, db
from config import Config, TestConfig


class CSRFEnabledConfig(TestConfig):
    WTF_CSRF_ENABLED = True
    UPLOAD_ROOT = Config.UPLOAD_ROOT / "test_csrf"
    PROFILE_UPLOAD_FOLDER = UPLOAD_ROOT / "profiles"
    POST_UPLOAD_FOLDER = UPLOAD_ROOT / "posts"


def _cleanup_uploads(root: Path | str) -> None:
    try:
        shutil.rmtree(Path(root))
    except FileNotFoundError:
        pass


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()
    _cleanup_uploads(app.config["UPLOAD_ROOT"])


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def csrf_app():
    app = create_app(CSRFEnabledConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()
    _cleanup_uploads(app.config["UPLOAD_ROOT"])


@pytest.fixture()
def csrf_client(csrf_app):
    return csrf_app.test_client()
