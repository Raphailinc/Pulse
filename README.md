# Pulse

![CI](https://github.com/Raphailinc/Pulse/actions/workflows/ci.yml/badge.svg)
![Coverage](https://raw.githubusercontent.com/Raphailinc/Pulse/main/badges/coverage.svg)

Мини-соцсеть на Flask с чистым API, безопасными загрузками и современной витриной.

## Скриншот
![Pulse UI](docs/pulse.svg)

## Что нового
- App factory + конфиги через переменные окружения (`DATABASE_URL`, `SECRET_KEY`), автоматическое создание директорий загрузок.
- Безопасное сохранение изображений (uuid, проверка расширений, лимит 5 МБ) для постов и профилей.
- Обновлённые шаблоны/стили: тёмный UI, поиск по ленте, карточки постов, удобный профиль.
- JSON эндпоинт `/api/posts` и улучшенная пагинация/поиск по ленте.
- Тесты на pytest с SQLite in-memory конфигом.

## Quickstart (Docker)
```bash
cp .env.example .env          # DATABASE_URL/SECRET_KEY можно оставить как есть
docker compose up --build
# API: http://localhost:8080/api/posts (HOST_PORT можно менять)
```

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
flask --app manage.py init-db   # создать таблицы
flask --app manage.py run
```

В Docker Compose используется PostgreSQL (см. `.env.example`). Для локального запуска без Docker можно оставить SQLite: `DATABASE_URL=sqlite:///social.db`. Пример для внешней БД:
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/pulse"
export SECRET_KEY="replace-me"
# HOST_PORT=8080  # можно поменять при использовании docker compose
```

## API (пример)
```bash
# JSON лента
GET /api/posts  -> {"posts": [{"id":1,"title":"First","author":"alice","image":null,...}]}

# Создать пост (формы)
POST /create_post title=Hello content="Hi" [image]

# Добавить комментарий
POST /post/<id>  content="Nice!"
```

## Архитектура
- `app/__init__.py` — фабрика, login manager, ensure uploads.
- `app/models.py` — Users/Posts/Comments, отношения и валидация.
- `app/routes.py` — HTML + JSON API, поиск/пагинация, загрузка медиа.
- `static/`, `templates/` — UI; `static/uploads` — медиа (монтируется как volume в Docker).
- `tests/` — pytest: регистрация/логин/посты/комменты.

## Линт и тесты
```bash
ruff check .
black --check .
pytest
```

## Возможности
- Регистрация/авторизация (пароли PBKDF2).
- Создание/редактирование/удаление постов с картинками.
- Комментарии, профиль с загрузкой аватара.
- Поиск и пагинация ленты, JSON выдача постов.
