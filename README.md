# Open Source APEX Equivalent

An open-source, metadata-driven application platform inspired by Oracle APEX: a
visual builder on top of a FastAPI rendering engine and a Next.js frontend.

- **Backend** — FastAPI + SQLAlchemy + Alembic (PostgreSQL). Renders pages,
  executes validations/processes/computations and exposes the builder API.
- **Frontend** — Next.js (App Router) visual builder and runtime preview.

## Quick start (Docker Compose)

```bash
cp .env.example .env      # optional
docker compose up --build
```

- Frontend: http://localhost:3000
- API + Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

The backend applies migrations on startup. To add the first administrator, see
the seeding step in [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md).

## Local development

```bash
# database
docker compose up -d postgres

# backend
cd backend
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload

# frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Testing

```bash
# backend (needs PostgreSQL; uses throwaway databases)
cd backend && python -m pytest -q -p no:cacheprovider --no-header

# frontend
cd frontend && npm test && npm run lint && npm run build
```

## Documentation

- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — phased roadmap
- [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) — deployment and configuration
- [docs/BUILDER_USER_GUIDE.md](./docs/BUILDER_USER_GUIDE.md) — using the builder
- [docs/API_REFERENCE.md](./docs/API_REFERENCE.md) — generated API reference
- [CONTRIBUTING.md](./CONTRIBUTING.md) — development workflow
- [RELEASE_NOTES.md](./RELEASE_NOTES.md) — MVP scope and verification
- [rapport_apex_architecture.docx](./rapport_apex_architecture.docx) — original specification

## Project structure

```
miniui/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # Versioned API endpoints
│   │   ├── core/            # Rendering engine, auth, caching, security
│   │   ├── db/              # Models and session management
│   │   └── schemas/         # Pydantic models
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend test suite
│   ├── dump_openapi.py      # Regenerate openapi.json
│   └── main.py              # ASGI entry point
├── frontend/                # Next.js visual builder
│   └── src/app/             # App Router pages, components and API services
├── docs/                    # Documentation
├── scripts/                 # init_db.py, API doc generation
├── docker-compose.yml       # PostgreSQL + backend + frontend
└── README.md
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Docker (optional, for the containerized stack)

## License

[To be determined]
