from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import HiddenField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms import ValidationError
from wtforms.validators import DataRequired, EqualTo, Length

from .images import inspect_image
from .models import User


def validate_image_file(form, field) -> None:
    file = field.data
    if not file or getattr(file, "filename", "") == "":
        field.data = None
        return
    try:
        inspect_image(file)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


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
