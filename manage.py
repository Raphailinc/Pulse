from __future__ import annotations

import os

from app import create_app, db

app = create_app()


@app.cli.command("init-db")
def init_db() -> None:
    """Create database tables."""
    with app.app_context():
        db.create_all()
        print("Database initialized")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", debug=debug, port=port)
