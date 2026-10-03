# Deployment Guide

Three services make up a deployment: PostgreSQL, the FastAPI backend, and the
Next.js frontend. The backend applies its own Alembic migrations on startup, so
a fresh database only needs to exist.

## Prerequisites

- Docker Engine 24+ with Docker Compose v2 (development and small deployments)
- Or, for host installs: Python 3.12+, Node.js 20+, PostgreSQL 15+

## Quick start with Docker Compose

```bash
cp .env.example .env        # optional: override defaults
docker compose up --build
```

| Service | URL | Notes |
| --- | --- | --- |
| Frontend | http://localhost:3000 | Next.js standalone server |
| Backend API | http://localhost:8000 | Swagger UI at `/docs` |
| Health | http://localhost:8000/health | Used by the container healthcheck |
| PostgreSQL | localhost:5432 | `apexos` / `apexos_user` / `apexos_pass` |

On startup the backend container runs `bootstrap.py`: it applies `alembic
upgrade head` (stamping legacy schemas first) and optionally seeds the first
administrator, then starts uvicorn. Compose waits for PostgreSQL to report
healthy and for the backend `/health` probe before starting the frontend. Both
images are self-contained; no source is bind-mounted by Compose. For live-reload
development run the backend and frontend on the host instead (see
[CONTRIBUTING.md](../CONTRIBUTING.md)).

## Environment variables

Set these for the backend (see `backend/.env.example`). Compose supplies the
defaults shown; a root `.env` file overrides them.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://apexos_user:apexos_pass@postgres:5432/apexos` | SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed browser origins |
| `ALLOWED_HOSTS` | `*` | Comma-separated `Host` allow-list; `*` disables the check |
| `COOKIE_SECURE` | `false` | Set `true` to mark the session cookie `Secure` (HTTPS only) |
| `METADATA_CACHE_TTL` | `5.0` | Seconds the application metadata export is cached |
| `METADATA_CACHE_MAX_ENTRIES` | `64` | Maximum entries in that cache |

The frontend reads `BACKEND_URL` (default `http://backend:8000` inside Compose)
for its server-side rewrites.

> `CORS_ORIGINS` and `ALLOWED_HOSTS` split on commas. In production set both to
> the real hostname(s) and serve the app over HTTPS with `COOKIE_SECURE=true`.

## Migrations

Migrations are automatic in Docker. To run them by hand:

```bash
# inside the backend container / backend directory
alembic upgrade head          # apply
alembic current               # inspect
alembic downgrade -1          # roll back one revision
```

`alembic/env.py` uses `DATABASE_URL` when the ini file still holds its built-in
localhost default, so the container and the host command line share one setting.

## Database initialization and the first administrator

Set `BOOTSTRAP_ADMIN_USERNAME`/`BOOTSTRAP_ADMIN_PASSWORD` (and optionally
`BOOTSTRAP_ADMIN_EMAIL`) on the backend service — for Compose, put them in the
root `.env` — and the administrator is created on the next startup. The same
routine is available on the host:

```bash
BOOTSTRAP_ADMIN_USERNAME=ADMIN \
BOOTSTRAP_ADMIN_PASSWORD='ChangeMe123!' \
BOOTSTRAP_ADMIN_EMAIL=admin@example.com \
python scripts/init_db.py
```

`scripts/init_db.py` and the container both call `backend/bootstrap.py`, which
also repairs databases created by an older `create_all` setup: if the tables
exist but no `alembic_version` row is present, the schema is stamped at the
current head before upgrading. The admin seed is idempotent: if the username
already exists it is left untouched.

## Health and readiness

`GET /health` returns `{"status": "ok", ...}` plus in-process metadata cache
statistics. It is a liveness probe: it does not touch the database, because
Compose and Kubernetes already gate on the database being up.

## Production checklist

- Set strong `POSTGRES_PASSWORD` and a `DATABASE_URL` that uses it.
- Set `ALLOWED_HOSTS` and `CORS_ORIGINS` to real domains; keep `*` only for local runs.
- Terminate TLS in front of the frontend and set `COOKIE_SECURE=true`.
- Run migrations as a dedicated step/job (the container already does it) so
  parallel replicas do not race on the schema.
- Back up the `postgres_data` volume; the API keeps no state outside PostgreSQL.

## Kubernetes

The images are the deployment unit (`backend/Dockerfile`, `frontend/Dockerfile`);
Compose is only a local convenience. A Kubernetes deployment needs the same two
containers plus a managed PostgreSQL, with `DATABASE_URL` supplied as a secret
and `/health` wired to the `livenessProbe`/`readinessProbe`. A Helm chart is not
part of this repository yet; until one exists, apply the manifests for the two
images directly and keep the migration-on-start behavior (or move it to an init
job if you scale the backend beyond one replica).
