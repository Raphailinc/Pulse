from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from PIL import Image, UnidentifiedImageError
from wtforms import HiddenField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms import ValidationError
from wtforms.validators import DataRequired, EqualTo, Length

from .models import User


def _allowed_formats() -> set[str]:
    configured = current_app.config.get("ALLOWED_IMAGE_FORMATS") or set()
    return {fmt.upper() for fmt in configured}


def validate_image_file(form, field) -> None:
    file = field.data
    if not file or getattr(file, "filename", "") == "":
        field.data = None
        return

    if not (file.mimetype or "").startswith("image/"):
        raise ValidationError("Разрешена загрузка только изображений.")

    try:
        file.stream.seek(0)
        image = Image.open(file.stream)
        image.verify()
        detected_format = (image.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("Файл не является допустимым изображением.") from exc

    allowed_formats = _allowed_formats()
    if detected_format not in allowed_formats:
        allowed_list = ", ".join(sorted(allowed_formats))
        raise ValidationError(f"Недопустимый формат. Разрешены: {allowed_list}")
    file.stream.seek(0)


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=64)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username is already in use. Please choose a different one.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=10)])
    image = FileField("Image", validators=[validate_image_file])
    current_image = HiddenField()
    submit = SubmitField("Post")


class CommentForm(FlaskForm):
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=2, max=500)])
    submit = SubmitField("Post Comment")


class UpdateProfileForm(FlaskForm):
    profile_picture = FileField("Update Profile Picture", validators=[validate_image_file])
    submit = SubmitField("Submit")
