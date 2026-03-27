# SvelteKit + FastAPI Template

This project includes:
- A FastAPI backend (`backend/`)
- A SvelteKit frontend (`frontend/`)
- Redis for cache/session-related storage
- Supabase-compatible PostgreSQL for local development
- Docker Compose setup for development and production-like runs

## Requirements

Install these tools on your machine:
- Docker (with Docker Compose)
- Node.js
- uv (Python package/dependency manager)

## Environment Setup

1. Create your local environment file from the template:

```bash
cp .env.template .env
```

2. Update values in `.env` if needed.

Notes:
- In development, Redis and Supabase-compatible DB run in Docker Compose.
- The backend uses `URL_DB` and defaults to the `supabase-db` service inside Compose.
- In production mode (`prod` service), frontend and backend run in the same container.

## Important Make Commands

Run this at any time to see all available commands:

```bash
make
```

### Development

- `make init`: Start dev services and run initial migrations.
- `make dev`: Start backend and frontend in detached mode.
- `make makemigrations-dev`: Create backend migrations.
- `make migrate-dev`: Apply backend migrations.
- `make logs`: Follow backend and frontend logs.
- `make ssh-back`: Open a shell in the backend dev container.
- `make ssh-front`: Open a shell in the frontend dev container.
- `make reset-dev`: Reset development environment (removes volumes).
- `make rebuild-dev`: Rebuild and start backend dev container.

### Production

- `make prod`: Build and start the `prod` container.
- `make logs-prod`: Follow `prod` logs.
- `make migrate-prod`: Apply backend migrations inside `prod`.
- `make ssh-prod`: Open a shell in `prod`.

## Backend Management Commands

Use `python manage.py <command>` to run backend management tasks:

### User Management

- `create_superuser`: Create a new superuser for a client database.
- `create_superuser_master`: Create a new superuser for the master database.
- `delete_user`: Delete a user from a client database.
- `delete_user_master`: Delete a user from the master database.

### Migrations

- `makemigrations`: Generate a new migration for a client database.
- `makemigrations_master`: Generate a new migration for the master database.
- `migrate`: Apply migrations to a client database.
- `migrate_master`: Apply migrations to the master database.

### Client Management

- `list_clients`: List all available clients in the master database.

## Production Database and Redis Options

Production can work in two ways:

1. Use local Supabase-compatible DB and Redis from this project

```bash
docker compose up -d supabase-db redis
make prod
```

2. Use external PostgreSQL and Redis (including Supabase cloud)

Set the connection URLs in `.env` to external services:
- `URL_DB`
- `URL_REDIS`

Then start production:

```bash
make prod
```

If your backend base URL must be customized, set `URL_BACKEND` in `.env` accordingly.
