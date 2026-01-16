from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import RequestEntityTooLarge

from .forms import CommentForm, LoginForm, PostForm, RegistrationForm, UpdateProfileForm
from .models import DEFAULT_PROFILE_IMAGE, Comment, Post, User, db

bp = Blueprint("app", __name__)

FORMAT_EXTENSION_MAP = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif"}


def _get_post_or_404(post_id: int) -> Post:
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    return post


def _get_comment_or_404(comment_id: int) -> Comment:
    comment = db.session.get(Comment, comment_id)
    if not comment:
        abort(404)
    return comment


def _allowed_formats() -> set[str]:
    configured = current_app.config.get("ALLOWED_IMAGE_FORMATS") or set()
    return {fmt.upper() for fmt in configured}


def _validate_image_upload(file_storage) -> tuple[Image.Image, str]:
    if not file_storage or file_storage.filename == "":
        raise ValueError("Выберите файл изображения.")
    if not (file_storage.mimetype or "").startswith("image/"):
        raise ValueError("Разрешена загрузка только изображений.")

    try:
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream)
        image.verify()
        image_format = (image.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Файл не является допустимым изображением.") from exc

    allowed_formats = _allowed_formats()
    if image_format not in allowed_formats:
        raise ValueError(f"Недопустимый формат. Разрешены: {', '.join(sorted(allowed_formats))}")

    file_storage.stream.seek(0)
    sanitized = Image.open(file_storage.stream)
    sanitized.load()
    return sanitized, image_format


def _prepare_image_for_save(image: Image.Image, image_format: str) -> Image.Image:
    if image_format == "JPEG":
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
    elif image_format in {"PNG", "WEBP"}:
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
    elif image_format == "GIF":
        if image.mode not in ("P", "L", "RGBA", "RGB"):
            image = image.convert("RGBA")
    return image


def _save_image(file_storage, folder_key: str) -> str | None:
    if not file_storage or file_storage.filename == "":
        return None

    image, image_format = _validate_image_upload(file_storage)
    image = _prepare_image_for_save(image, image_format)

    target_dir = Path(current_app.config[folder_key])
    target_dir.mkdir(parents=True, exist_ok=True)

    extension = FORMAT_EXTENSION_MAP.get(image_format, f".{image_format.lower()}")
    filename = f"{uuid4().hex}{extension}"
    path = target_dir / filename

    save_kwargs = {"format": image_format}
    if image_format == "JPEG":
        save_kwargs.update({"quality": 85, "optimize": True})

    image.save(path, **save_kwargs)

    static_root = Path(current_app.static_folder).resolve()
    try:
        relative = path.resolve().relative_to(static_root)
    except ValueError as exc:
        raise RuntimeError("Upload path is misconfigured.") from exc
    return relative.as_posix()


def _delete_file(relative_path: str | None) -> None:
    if not relative_path:
        return

    rel_path = Path(relative_path)
    if rel_path.is_absolute():
        current_app.logger.warning("Attempt to delete absolute path %s was blocked.", rel_path)
        return

    uploads_root = Path(current_app.config["UPLOAD_ROOT"]).resolve()
    target = (Path(current_app.static_folder) / rel_path).resolve()
    if uploads_root not in target.parents and target != uploads_root:
        current_app.logger.warning("Attempt to delete file outside uploads dir: %s", target)
        return

    try:
        target.unlink()
    except FileNotFoundError:
        return


@bp.route("/")
def home():
    recent_posts = (
        Post.query.options(joinedload(Post.user)).order_by(Post.date_posted.desc()).limit(6).all()
    )
    return render_template("home.html", posts=recent_posts)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("app.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method="pbkdf2:sha256")
        new_user = User(username=form.username.data.strip(), password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Аккаунт создан!", "success")
            return redirect(url_for("app.login"))
        except IntegrityError:
            db.session.rollback()
            flash("Имя пользователя уже занято.", "danger")
    return render_template("register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("app.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Успешный вход!", "success")
            return redirect(url_for("app.home"))
        flash("Неверное имя пользователя или пароль.", "danger")
    return render_template("login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("app.home"))


@bp.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    status_code = 200
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            try:
                image_path = _save_image(form.image.data, "POST_UPLOAD_FOLDER")
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("create_post.html", form=form), 400

        post = Post(
            title=form.title.data.strip(),
            content=form.content.data.strip(),
            user=current_user,
            image=image_path,
        )
        db.session.add(post)
        db.session.commit()
        flash("Пост опубликован!", "success")
        return redirect(url_for("app.all_posts"))
    if request.method == "POST":
        status_code = 400
    return render_template("create_post.html", form=form), status_code


@bp.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    post = _get_post_or_404(post_id)
    if post.user != current_user:
        abort(403)

    form = PostForm(obj=post)
    if form.validate_on_submit():
        previous_image = post.image
        new_image_path = None
        if form.image.data:
            try:
                new_image_path = _save_image(form.image.data, "POST_UPLOAD_FOLDER")
            except ValueError as exc:
                flash(str(exc), "danger")
                db.session.rollback()
                return render_template("edit_post.html", form=form, post=post), 400
        post.title = form.title.data.strip()
        post.content = form.content.data.strip()
        if new_image_path:
            post.image = new_image_path
        db.session.commit()
        if new_image_path and previous_image and new_image_path != previous_image:
            _delete_file(previous_image)
        flash("Пост обновлён.", "success")
        return redirect(url_for("app.view_post", post_id=post.id))

    if request.method == "GET":
        form.current_image.data = post.image or ""
    if request.method == "POST":
        return render_template("edit_post.html", form=form, post=post), 400
    return render_template("edit_post.html", form=form, post=post)


@bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def view_post(post_id: int):
    post = Post.query.options(joinedload(Post.user)).filter_by(id=post_id).first_or_404()
    form = CommentForm()
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Войдите, чтобы оставлять комментарии.", "danger")
            return redirect(url_for("app.login"))
        if form.validate_on_submit():
            comment = Comment(content=form.content.data.strip(), post=post, user=current_user)
            db.session.add(comment)
            db.session.commit()
            flash("Комментарий добавлен!", "success")
            return redirect(url_for("app.view_post", post_id=post_id))

    comments = (
        Comment.query.options(joinedload(Comment.user))
        .filter_by(post_id=post.id)
        .order_by(Comment.date_created.desc())
        .all()
    )
    return render_template("view_post.html", post=post, comments=comments, form=form)


@bp.route("/all_posts")
def all_posts():
    search_query = (request.args.get("search") or "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 6

    query = Post.query.options(joinedload(Post.user)).order_by(Post.date_posted.desc())
    if search_query:
        query = query.filter(
            Post.title.ilike(f"%{search_query}%") | Post.content.ilike(f"%{search_query}%")
        )

    posts = query.paginate(page=page, per_page=per_page, error_out=False)
    form = CommentForm()
    return render_template("all_posts.html", posts=posts, form=form, search=search_query)


@bp.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = _get_post_or_404(post_id)
    if current_user != post.user:
        abort(403)
    image_path = post.image
    db.session.delete(post)
    db.session.commit()
    _delete_file(image_path)
    flash("Пост удалён.", "success")
    return redirect(url_for("app.all_posts"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateProfileForm()
    user = current_user
    status_code = 200

    if form.validate_on_submit() and form.profile_picture.data:
        previous_image = user.profile_image
        try:
            saved = _save_image(form.profile_picture.data, "PROFILE_UPLOAD_FOLDER")
            user.profile_image = saved
            db.session.commit()
            if previous_image and previous_image != DEFAULT_PROFILE_IMAGE:
                _delete_file(previous_image)
            flash("Фото профиля обновлено.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
            status_code = 400

    if request.method == "POST" and form.errors:
        status_code = 400

    posts = (
        Post.query.filter_by(user_id=user.id)
        .order_by(Post.date_posted.desc())
        .options(joinedload(Post.comments))
        .all()
    )
    return render_template("profile.html", user=user, posts=posts, form=form), status_code


@bp.route("/edit_comment/<int:comment_id>", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id: int):
    comment = _get_comment_or_404(comment_id)
    if comment.user != current_user:
        abort(403)
    form = CommentForm(obj=comment)
    if form.validate_on_submit():
        comment.content = form.content.data.strip()
        db.session.commit()
        flash("Комментарий обновлён.", "success")
        return redirect(url_for("app.view_post", post_id=comment.post.id))
    return render_template("edit_comment.html", form=form, comment=comment)


@bp.route("/delete_comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id: int):
    comment = _get_comment_or_404(comment_id)
    if comment.user != current_user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("Комментарий удалён.", "success")
    return redirect(url_for("app.view_post", post_id=comment.post_id))


@bp.app_errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "File too large"}), 413
    flash("Файл превышает допустимый размер загрузки.", "danger")
    return redirect(request.referrer or url_for("app.home")), 413


@bp.route("/api/posts")
def api_posts():
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    limit = request.args.get("limit", 20, type=int) or 20
    if limit <= 0:
        limit = 20
    limit = min(limit, 100)

    pagination = (
        Post.query.options(joinedload(Post.user))
        .order_by(Post.date_posted.desc())
        .paginate(page=page, per_page=limit, error_out=False)
    )
    items = [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "author": p.user.username,
            "created_at": p.date_posted.isoformat(),
            "image": p.image_url(),
        }
        for p in pagination.items
    ]
    return jsonify(
        {
            "items": items,
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages or 0,
        }
    )
