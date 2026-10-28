# Pulse

[![CI](https://github.com/Raphailinc/Pulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Raphailinc/Pulse/actions/workflows/ci.yml)

[English](README.md) · [Русский](README.ru.md)

Социальное приложение на Flask: структура приложения, авторизация, пользовательский контент и HTML/JSON-маршруты.

## Возможности

- Регистрация и вход с хешированием паролей и CSRF-защитой форм.
- Посты, комментарии и профили с проверками прав владельца.
- Проверка содержимого, формата, размера файла и числа пикселей до сохранения изображения.
- Поиск, пагинация и JSON API /api/posts.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
# Set a locally generated SECRET_KEY in .env before running the app.
flask --app manage.py init-db
flask --app manage.py run
```

## Проверки

```bash
python -m pytest
ruff check .
black --check .
```

## Условия запуска и границы проекта

Нужен Python 3.11+. Интерфейс: http://127.0.0.1:5000. Перед запуском задайте SECRET_KEY в .env: python -c "import secrets; print(secrets.token_hex(32))". SQLite используется локально, PostgreSQL — в Compose. MAX_IMAGE_PIXELS по умолчанию ограничивает изображение 16 миллионами пикселей. Проверка изображений общая для форм и сохранения; она не заменяет антивирусную проверку в production.
