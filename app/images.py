"""Validate image headers before decoding or persisting uploads."""

import warnings

from flask import current_app
from PIL import Image, UnidentifiedImageError


def inspect_image(upload) -> str:
    if not upload or not upload.filename:
        raise ValueError("Выберите файл изображения.")
    if not (upload.mimetype or "").startswith("image/"):
        raise ValueError("Разрешена загрузка только изображений.")

    upload.stream.seek(0)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload.stream) as image:
                if image.width * image.height > current_app.config["MAX_IMAGE_PIXELS"]:
                    raise ValueError("Изображение превышает допустимое число пикселей.")
                image_format = (image.format or "").upper()
                allowed = {fmt.upper() for fmt in current_app.config["ALLOWED_IMAGE_FORMATS"]}
                if image_format not in allowed:
                    raise ValueError(
                        f"Недопустимый формат. Разрешены: {', '.join(sorted(allowed))}"
                    )
                image.verify()
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError("Файл не является допустимым изображением.") from exc
    finally:
        upload.stream.seek(0)
    return image_format


def load_image(upload) -> tuple[Image.Image, str]:
    image_format = inspect_image(upload)
    try:
        with Image.open(upload.stream) as image:
            image.load()
            sanitized = image.copy()
    except OSError as exc:
        raise ValueError("Файл изображения повреждён.") from exc
    finally:
        upload.stream.seek(0)
    return sanitized, image_format
