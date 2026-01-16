from __future__ import annotations

from app import db
from app.models import Comment, Post, User


def login_session(client, user_id: int) -> None:
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def test_logout_requires_csrf(csrf_app, csrf_client):
    with csrf_app.app_context():
        user = User(username="alice", password="hash")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    login_session(csrf_client, user_id)
    resp = csrf_client.post("/logout")
    assert resp.status_code == 400


def test_delete_post_requires_csrf(csrf_app, csrf_client):
    with csrf_app.app_context():
        user = User(username="owner", password="hash")
        post = Post(title="Title", content="content body", user=user)
        db.session.add_all([user, post])
        db.session.commit()
        user_id = user.id
        post_id = post.id

    login_session(csrf_client, user_id)
    resp = csrf_client.post(f"/delete_post/{post_id}")
    assert resp.status_code == 400
    with csrf_app.app_context():
        assert db.session.get(Post, post_id) is not None


def test_delete_comment_requires_csrf(csrf_app, csrf_client):
    with csrf_app.app_context():
        user = User(username="owner", password="hash")
        post = Post(title="Title", content="content body", user=user)
        comment = Comment(content="Hello", post=post, user=user)
        db.session.add_all([user, post, comment])
        db.session.commit()
        user_id = user.id
        comment_id = comment.id

    login_session(csrf_client, user_id)
    resp = csrf_client.post(f"/delete_comment/{comment_id}")
    assert resp.status_code == 400
    with csrf_app.app_context():
        assert db.session.get(Comment, comment_id) is not None


def test_forbid_deleting_foreign_post(client, app):
    with app.app_context():
        owner = User(username="owner", password="hash")
        intruder = User(username="intruder", password="hash2")
        post = Post(title="Protected", content="body content", user=owner)
        db.session.add_all([owner, intruder, post])
        db.session.commit()
        intruder_id = intruder.id
        post_id = post.id

    login_session(client, intruder_id)
    resp = client.post(f"/delete_post/{post_id}")
    assert resp.status_code == 403
    with app.app_context():
        assert db.session.get(Post, post_id) is not None


def test_forbid_deleting_foreign_comment(client, app):
    with app.app_context():
        owner = User(username="owner", password="hash")
        post = Post(title="Post", content="content body", user=owner)
        commenter = User(username="commenter", password="hash2")
        comment = Comment(content="Nice post", post=post, user=owner)
        db.session.add_all([owner, commenter, post, comment])
        db.session.commit()
        commenter_id = commenter.id
        comment_id = comment.id

    login_session(client, commenter_id)
    resp = client.post(f"/delete_comment/{comment_id}")
    assert resp.status_code == 403
    with app.app_context():
        assert db.session.get(Comment, comment_id) is not None


def test_comment_requires_authentication(client, app):
    with app.app_context():
        owner = User(username="owner", password="hash")
        post = Post(title="Post", content="content body", user=owner)
        db.session.add_all([owner, post])
        db.session.commit()
        post_id = post.id

    resp = client.post(f"/post/{post_id}", data={"content": "Hi"})
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("Location", "")
    with app.app_context():
        assert Comment.query.count() == 0
