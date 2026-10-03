# Phase 7: Testing and Quality Assurance - Summary

## Result

| Surface | Result |
| --- | --- |
| Backend tests (PostgreSQL) | 421 passed |
| Frontend tests (Vitest + Testing Library) | 108 passed |
| Frontend type check (`npm run lint` -> `tsc --noEmit`) | clean |
| Frontend production build (`npm run build`) | compiled successfully |
| Alembic migrations | linear, single head `b3c4d5e6f7a8` |
| OpenAPI contract | regenerated, frontend route-contract test green |

Commands:

```powershell
# backend
cd backend
docker compose up -d postgres
python -m pytest -q -p no:cacheprovider --no-header

# frontend
cd frontend
npm test
npm run lint
npm run build
```

## What was added

### Backend test suites

| File | Coverage |
| --- | --- |
| `tests/test_auth.py` | login/logout, session binding, account lockout, admin unlock, password hashing, session cookies on runtime pages |
| `tests/test_e2e_flow.py` | full HTTP lifecycle: build page, render, submit, validation errors, process redirect, report rows, cleanup |
| `tests/test_cache_and_performance.py` | TTL cache unit tests, metadata endpoint cache/invalidation/expiry, index existence, render and export budgets |
| `tests/test_middleware.py` | CSRF exemption rules, rate limiting |
| `tests/test_page_builder.py` | builder route order, role enforcement, page lifecycle |
| `tests/test_processes_computations.py` | process execution points and computation engine |
| `tests/test_validation_types.py` | validation types and messages |
| `tests/test_crud.py` | CRUD pagination and scoping |
| `tests/test_item_types.py`, `tests/test_region_types.py` | item/region renderers |
| `tests/test_migrations.py` | migration chain, schema drift, session-state data remap |

The database fixture creates a throwaway PostgreSQL database per session and
rolls back each test through savepoints (`tests/database.py`, `tests/conftest.py`).

### Bugs found and fixed while adding tests

- `render.py` referenced `page.title`, a column that does not exist, so
  `GET /app/{alias}/{number}` raised a 500. Now uses `page.name`.
- The rendered form posted to `/ords/apex/...` with a `p_session_id` field, which
  no endpoint accepts. The action now points at `/api/v1/pages/{alias}/{number}`
  and the runtime endpoint also accepts `p_session_id` as an alias.
- The default post-submit redirect pointed at `/{alias}/{number}`, which is not a
  route. It now points at `/api/v1/pages/{alias}/{number}`.
- `authenticate_user` had unreachable "unlock on success" code that implied a
  locked account could unlock itself. The dead branch was removed; recovery is an
  explicit ADMIN action through the workspace-user endpoint.

### Performance

- `app/core/cache.py`: a thread-safe in-process TTL cache, no new dependency.
  The application metadata export is cached for a few seconds
  (`METADATA_CACHE_TTL`, default 5s) and invalidated on application update/delete.
  Only plain JSON-ready data is cached, never ORM objects.
- Migration `b3c4d5e6f7a8` and matching `app/db/models.py` declarations add the
  missing lookup indexes: `(application_id, page_number)` on pages and `page_id`
  on regions, items, processes, computations and validations.

## Not done / next

- End-to-end tests exercise the backend HTTP API, not a real browser. A
  Playwright/Cypress layer is the natural next step if UI flows need coverage.
- `flake8` still reports pre-existing style findings (long lines, unused imports);
  they were out of scope for this phase.
- `frontend` depends on the backend for real data; the builder test mocks the
  service layer.
