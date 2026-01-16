from __future__ import annotations

import secrets
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from config import Config
from .models import User, db
from .routes import bp

csrf = CSRFProtect()


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        if app.config.get("TESTING"):
            app.config["SECRET_KEY"] = secrets.token_hex(16)
        else:
            raise RuntimeError("SECRET_KEY is required. Set SECRET_KEY environment variable.")

    # Ensure upload directories exist
    for key in ("UPLOAD_ROOT", "PROFILE_UPLOAD_FOLDER", "POST_UPLOAD_FOLDER"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "app.login"
    login_manager.login_message_category = "danger"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    app.register_blueprint(bp)
    return app
