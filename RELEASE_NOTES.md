# Release Notes

## v0.1.0 — MVP

First end-to-end release: build a simple data-driven application in the browser and
run it.

### Highlights

- **Metadata-driven runtime** — pages, regions, items, validations, processes,
  computations and LOVs are stored as data and rendered by the engine.
- **Visual builder** — create applications and pages, drag regions and items,
  edit properties, and preview the rendered page.
- **Security** — username/password login with server-side sessions and an
  HttpOnly cookie, account lockout, ADMIN/DEVELOPER/END_USER roles, per-page
  visibility, CSRF header enforcement, security headers and login rate limiting.
- **REST data sources** — store and execute external HTTP endpoints from the
  builder.
- **Operations ready** — Docker Compose stack, migrations applied on backend
  startup, `/health` probe, metadata caching and database indexes.

### MVP verification checklist

| Requirement (Phase 8.3) | Where it is verified |
| --- | --- |
| Create simple data-driven applications | `backend/tests/test_page_builder.py`, `test_crud.py`; `frontend/.../builder/[appId]/page.test.tsx` |
| Basic form and report regions | `backend/tests/test_region_types.py`, `test_e2e_flow.py` |
| Session state management | `backend/tests/test_auth.py`, `test_e2e_flow.py` |
| Visual builder for creating pages | `frontend/.../builder/[appId]/page.test.tsx` |
| Database authentication | `backend/tests/test_auth.py` |
| Migrations apply cleanly | `backend/tests/test_migrations.py` |
| Deployment / health | `backend/tests/test_health.py`, `docker compose up --build` |

### Verification performed

| Check | Result |
| --- | --- |
| `python -m pytest` (backend, PostgreSQL) | 425 passed |
| `npm test` (frontend, Vitest) | 108 passed |
| `npm run lint` (`tsc --noEmit`) | clean |
| `npm run build` | compiled successfully |

### Known limitations

- No browser-driven E2E layer (Playwright/Cypress); the end-to-end tests exercise
  the HTTP API.
- Reports are read-only result sets; editable grids, charts, trees, calendars and
  maps are post-MVP stretch goals.
- No self-service registration, application export/import, or Helm chart yet.
- `flake8` still reports pre-existing style findings.

See `IMPLEMENTATION_PLAN.md` for the roadmap.
