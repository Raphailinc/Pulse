from __future__ import annotations

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
    app.run(debug=True)
