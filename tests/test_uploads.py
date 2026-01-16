from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from app import db
from app.models import Post


def register_and_login(client, username: str = "alice", password: str = "secret123"):
    client.post(
        "/register",
        data={"username": username, "password": password, "confirm_password": password},
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def make_image_bytes(
    fmt: str = "PNG", size: tuple[int, int] = (32, 32), color=(255, 0, 0)
) -> BytesIO:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    buf.seek(0)
    return buf


def test_reject_invalid_image_upload(client, app):
    register_and_login(client)
    bad_file = (BytesIO(b"not an image"), "fake.png", "image/png")
    resp = client.post(
        "/create_post",
        data={"title": "Bad", "content": "content goes here", "image": bad_file},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    with app.app_context():
        assert Post.query.count() == 0


def test_reject_too_large_upload(client, app):
    register_and_login(client)
    app.config["MAX_CONTENT_LENGTH"] = 1024  # 1 KB
    large_image = (make_image_bytes(size=(200, 200)), "large.png", "image/png")

    resp = client.post(
        "/create_post",
        data={"title": "Big", "content": "content goes here", "image": large_image},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 413


def test_valid_image_saved_and_normalized(client, app):
    register_and_login(client)
    uploaded = (make_image_bytes(fmt="PNG", size=(40, 40)), "weird.txt", "image/png")
    resp = client.post(
        "/create_post",
        data={"title": "Image", "content": "content goes here", "image": uploaded},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        post = Post.query.first()
        assert post is not None
        saved_path = Path(app.static_folder) / post.image
        assert saved_path.exists()
        saved_image = Image.open(saved_path)
        assert saved_image.format == "PNG"


def test_file_cleanup_on_replace_and_delete(client, app):
    register_and_login(client)
    first_image = (make_image_bytes(color=(255, 0, 0)), "first.png", "image/png")
    client.post(
        "/create_post",
        data={"title": "File post", "content": "content goes here", "image": first_image},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    with app.app_context():
        post = Post.query.first()
        assert post and post.image
        post_id = post.id
        first_path = Path(app.static_folder) / post.image
        assert first_path.exists()

    replacement = (make_image_bytes(color=(0, 255, 0)), "second.png", "image/png")
    resp = client.post(
        f"/edit_post/{post_id}",
        data={"title": "Updated", "content": "updated content here", "image": replacement},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        post = db.session.get(Post, post_id)
        assert post and post.image
        new_path = Path(app.static_folder) / post.image
        assert not first_path.exists()
        assert new_path.exists()

    resp = client.post(f"/delete_post/{post_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert not new_path.exists()
