from __future__ import annotations

from app import db
from app.models import Post, User


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
    assert "items" in payload
    assert payload["items"][0]["title"] == "API Post"
    assert payload["page"] == 1
    assert payload["total"] == 1


def test_api_posts_limit_cap(client, app):
    with app.app_context():
        user = User(username="bulk", password="hash")
        db.session.add(user)
        for i in range(120):
            db.session.add(Post(title=f"Post {i}", content="content body", user=user))
        db.session.commit()

    resp = client.get("/api/posts?limit=150&page=2")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["limit"] == 100
    assert payload["page"] == 2
    assert payload["total"] == 120
    assert len(payload["items"]) == 20
