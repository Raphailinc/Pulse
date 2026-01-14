from __future__ import annotations

import pytest

from app import create_app, db
from app.models import Post, User
from config import TestConfig


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username: str, password: str):
    return client.post(
        "/register",
        data={"username": username, "password": password, "confirm_password": password},
        follow_redirects=True,
    )


def login(client, username: str, password: str):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_register_and_login_flow(client, app):
    rv = register(client, "alice", "secret123")
    body = rv.get_data(as_text=True)
    assert "Аккаунт создан" in body

    rv = login(client, "alice", "secret123")
    assert "Успешный вход" in rv.get_data(as_text=True)


def test_create_post_and_comment(client, app):
    register(client, "alice", "secret123")
    login(client, "alice", "secret123")

    rv = client.post(
        "/create_post",
        data={"title": "First", "content": "Hello world content"},
        follow_redirects=True,
    )
    assert "Пост опубликован" in rv.get_data(as_text=True)

    with app.app_context():
        post_id = Post.query.first().id

    rv = client.post(
        f"/post/{post_id}",
        data={"content": "Nice post"},
        follow_redirects=True,
    )
    assert "Комментарий добавлен" in rv.get_data(as_text=True)


def test_api_posts(client, app):
    with app.app_context():
        user = User(username="bob", password="hash")
        db.session.add(user)
        db.session.add(Post(title="API Post", content="content", user=user))
        db.session.commit()

    resp = client.get("/api/posts")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "posts" in payload
    assert payload["posts"][0]["title"] == "API Post"
