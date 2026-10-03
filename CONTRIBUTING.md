# Contributing

Thanks for helping improve this open-source APEX equivalent.

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ (or Docker)

## Local development

### Database

```bash
docker compose up -d postgres
```

### Backend

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # adjust DATABASE_URL if needed
alembic upgrade head
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000, proxies the API to :8000
```

## Tests

Backend (needs PostgreSQL reachable; the suite creates and drops its own scratch
databases, so it is safe to run while the app is up):

```bash
cd backend
python -m pytest -q -p no:cacheprovider --no-header
```

Frontend:

```bash
cd frontend
npm test                    # vitest run
npm run test:coverage
npm run lint                # tsc --noEmit
npm run build
```

All of the above must pass before opening a pull request.

## Style

- Python: formatted with `black` and `isort`; keep functions and modules small.
  `flake8` reports pre-existing long-line/unused-import findings, so run it but
  do not treat its full output as a gate.
- TypeScript/React: functional components and hooks; no `any` unless unavoidable;
  `npm run lint` is the type gate.
- Tests live next to what they test; prefer behavior over implementation details.

## Database changes

Create migrations with Alembic; never edit an applied revision.

```bash
cd backend
alembic revision --autogenerate -m "add <thing>"
alembic upgrade head
```

Add or update a test in `backend/tests/test_migrations.py` for any schema change
(the suite asserts there is a single head and that models match the migrated
schema).

## API changes

`backend/openapi.json` is the contract the frontend is tested against. After
changing a route or schema:

```bash
cd backend && python dump_openapi.py
cd .. && python scripts/generate_api_docs.py
```

Commit both the regenerated `openapi.json` and `docs/API_REFERENCE.md`.

## Commits and pull requests

- Keep commits focused; the repository history uses short, lowercase summaries
  such as `phase 7: testing, performance and bug fixes`.
- Describe what changed and why in the PR, and list the commands you ran to
  verify it.
- Do not commit secrets, `.env` files, local databases or logs (see
  `.gitignore`).
