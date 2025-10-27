# Fullstack App Docker Compose Lab

## Overview
This lab packages a Flask REST API, PostgreSQL database, Redis cache, and Adminer UI into a single Docker Compose stack. The `web` service exposes CRUD endpoints for user management, persists records in PostgreSQL, and caches list responses in Redis.

## Stack Components
- **web**: Flask application served by Gunicorn (`http://localhost:5000`).
- **db**: PostgreSQL 15 with persistent volume.
- **cache**: Redis 7 used for session and list caching.
- **adminer**: Lightweight UI for inspecting the database (`http://localhost:8080`).

```
fullstack-app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   └── routes.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── wsgi.py
```

## Prerequisites
- Docker Engine 24+
- Docker Compose plugin 2+

## Environment Variables
`docker-compose.yml` wires the services with the following defaults:

| Variable | Service | Default | Purpose |
|----------|---------|---------|---------|
| `DATABASE_URL` | web | `postgresql://app_user:app_password@db:5432/user_db` | SQLAlchemy connection URI |
| `POSTGRES_USER` | db | `app_user` | Database role |
| `POSTGRES_PASSWORD` | db | `app_password` | Role password |
| `POSTGRES_DB` | db | `user_db` | Default database |
| `REDIS_HOST` | web | `cache` | Redis hostname |
| `REDIS_PORT` | web | `6379` | Redis port |

Update these values in `docker-compose.yml` or move them into an `.env` file before running in production.

## Running the Stack
1. **Optional**: Reset persisted data if credentials changed.
```bash
    docker compose down -v
```
2. Build and start all services in detached mode.
```bash
    docker compose up --build -d
```
3. Tail the web logs if needed.
```bash
    docker compose logs -f web
```

## Health Checks
- Application: `curl http://localhost:5000/health`
- PostgreSQL: `docker compose exec db pg_isready -U app_user -d user_db`
- Redis: `docker compose exec cache redis-cli ping`

## API Endpoints
All routes are prefixed with `/users`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users` | Create a user. Body: `{ "name": "Alice", "email": "alice@example.com" }` |
| `GET` | `/users` | List users (uses Redis cache). |
| `GET` | `/users/<id>` | Retrieve a user by ID. |
| `PUT` | `/users/<id>` | Update name and/or email. |
| `DELETE` | `/users/<id>` | Remove a user. |

### Example Usage
Create a user:
```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

List users:
```bash
curl http://localhost:5000/users
```

## Adminer Access
1. Open `http://localhost:8080`.
2. Choose **System**: PostgreSQL.
3. Use the credentials:
   - Server: `db`
   - Username: `app_user`
   - Password: `app_password`
   - Database: `user_db`

## Troubleshooting
- Ensure the database volume matches the configured credentials. If the password was changed, reset with `docker compose down -v`.
- Use `docker compose ps` to confirm service health states.
- For dependency updates, edit `requirements.txt` and rerun `docker compose up --build -d`.
