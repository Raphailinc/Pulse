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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .forms import CommentForm, LoginForm, PostForm, RegistrationForm, UpdateProfileForm
from .models import Comment, Post, User, db

bp = Blueprint("app", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _save_image(file_storage, folder_key: str) -> str | None:
    if not file_storage or file_storage.filename == "":
        return None

    filename = secure_filename(file_storage.filename)
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Недопустимый формат изображения.")

    target_dir = Path(current_app.config[folder_key])
    target_dir.mkdir(parents=True, exist_ok=True)

    new_name = f"{uuid4().hex}{Path(filename).suffix.lower()}"
    path = target_dir / new_name
    file_storage.save(path)
    relative = path.relative_to(Path(current_app.static_folder))
    return f"{relative.as_posix()}"


@bp.route("/")
def home():
    recent_posts = (
        Post.query.options(joinedload(Post.user))
        .order_by(Post.date_posted.desc())
        .limit(6)
        .all()
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


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("app.home"))


@bp.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            try:
                image_path = _save_image(form.image.data, "POST_UPLOAD_FOLDER")
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("create_post.html", form=form)

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
    return render_template("create_post.html", form=form)


@bp.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.user != current_user:
        abort(403)

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.content = form.content.data.strip()
        if form.image.data:
            try:
                post.image = _save_image(form.image.data, "POST_UPLOAD_FOLDER")
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("edit_post.html", form=form, post=post)
        db.session.commit()
        flash("Пост обновлён.", "success")
        return redirect(url_for("app.view_post", post_id=post.id))

    if request.method == "GET":
        form.current_image.data = post.image or ""
    return render_template("edit_post.html", form=form, post=post)


@bp.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def view_post(post_id: int):
    post = (
        Post.query.options(joinedload(Post.user), joinedload(Post.comments).joinedload(Comment.user))
        .filter_by(id=post_id)
        .first_or_404()
    )
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data.strip(), post=post, user=current_user)
        db.session.add(comment)
        db.session.commit()
        flash("Комментарий добавлен!", "success")
        return redirect(url_for("app.view_post", post_id=post_id))
    comments = post.comments.order_by(Comment.date_created.desc()).all()
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
    post = Post.query.get_or_404(post_id)
    if current_user != post.user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Пост удалён.", "success")
    return redirect(url_for("app.all_posts"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateProfileForm()
    user = current_user

    if form.validate_on_submit() and form.profile_picture.data:
        try:
            saved = _save_image(form.profile_picture.data, "PROFILE_UPLOAD_FOLDER")
            user.profile_image = saved
            db.session.commit()
            flash("Фото профиля обновлено.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")

    posts = (
        Post.query.filter_by(user_id=user.id)
        .order_by(Post.date_posted.desc())
        .options(joinedload(Post.comments))
        .all()
    )
    return render_template("profile.html", user=user, posts=posts, form=form)


@bp.route("/edit_comment/<int:comment_id>", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id: int):
    comment = Comment.query.get_or_404(comment_id)
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
    comment = Comment.query.get_or_404(comment_id)
    if comment.user != current_user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("Комментарий удалён.", "success")
    return redirect(url_for("app.view_post", post_id=comment.post_id))


@bp.route("/api/posts")
def api_posts():
    posts = (
        Post.query.options(joinedload(Post.user))
        .order_by(Post.date_posted.desc())
        .limit(20)
        .all()
    )
    payload = [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "author": p.user.username,
            "created_at": p.date_posted.isoformat(),
            "image": p.image_url(),
        }
        for p in posts
    ]
    return jsonify({"posts": payload})
