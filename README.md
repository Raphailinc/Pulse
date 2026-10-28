# Pulse

[![CI](https://github.com/Raphailinc/Pulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Raphailinc/Pulse/actions/workflows/ci.yml)

[English](README.md) · [Русский](README.ru.md)

A small social application used to explore Flask application structure, user-owned content and HTML/JSON endpoints.

## What it does

- Register and sign in with hashed passwords and CSRF-protected forms.
- Create posts, comments and profiles, with ownership checks for edits.
- Store images under generated names with extension and size checks.
- Search and paginate the feed; query `/api/posts` as JSON.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
# Set a locally generated SECRET_KEY in .env before running the app.
flask --app manage.py init-db
flask --app manage.py run
```

## Checks

```bash
python -m pytest
ruff check .
black --check .
```

## Scope and implementation notes

Local UI: `http://127.0.0.1:5000`. Use `python -c "import secrets; print(secrets.token_hex(32))"` to generate a secret for your local `.env`. SQLite is the default; Docker Compose uses PostgreSQL. This is a portfolio app; upload validation does not replace a production malware-scanning service.
