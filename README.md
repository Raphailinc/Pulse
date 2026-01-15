# Pulse

![CI](https://github.com/Raphailinc/Pulse/actions/workflows/ci.yml/badge.svg)

Мини-соцсеть на Flask с чистым API, безопасными загрузками и современной витриной.

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
# API: http://localhost:8000/api/posts
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
```

## Структура
- `app/__init__.py` — фабрика приложения, логин-менеджер, регистрация blueprint.
- `app/models.py` — пользователи, посты, комментарии с каскадным удалением.
- `app/routes.py` — все маршруты, поиск, пагинация, API, загрузка медиа.
- `static/styles.css` — новый UI; `static/uploads/...` — хранилище изображений.
- `templates/` — обновлённые страницы (лента, пост, профиль, auth).
- `tests/` — pytest сценарии регистрация/логин/пост/комментарий.

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
