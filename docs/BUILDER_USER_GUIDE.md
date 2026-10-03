# Visual Builder User Guide

A short walkthrough of building and running an application in the browser.

## 1. Sign in

Open http://localhost:3000 and sign in at `/auth/login` with a workspace user
(see [DEPLOYMENT.md](./DEPLOYMENT.md) for creating the first administrator).
On success the backend sets the `miniui_session` cookie; the SPA also keeps the
session token for API calls.

## 2. Applications

`/apps` lists the applications you can access.

- **New application** (`/apps/new`) creates one. Required fields: a unique
  `alias` (used in runtime URLs) and a `name`; optional `description` and
  `theme`. Only `ADMIN` and `DEVELOPER` roles may create or edit applications.
- Selecting an application opens the **application builder**
  (`/apps/builder/{appId}`), where you can edit its metadata and manage its
  pages, list of values (LOVs) and REST data sources.

## 3. Pages

From the application builder:

- **Add page** (`/apps/builder/{appId}/pages/new`) asks for a name, alias, title,
  page number and the `is_active` flag. The number and alias are pre-filled with
  the next free value.
- Clicking a page opens the **visual page builder**
  (`/apps/builder/{appId}/pages/{pageId}`).

### Visual page builder

The canvas uses drag-and-drop plus a property inspector:

1. Drag a **region** onto the page (for example a form, report or static HTML
   region) and set its type and source in the inspector.
2. Drag **items** into a region to add fields (text, select, radio, checkbox and
   so on). Select any region or item to edit its properties; unsaved changes are
   tracked per element.
3. Optionally attach **validations** to items or pages, **processes** to
   execution points (before header, after submit, …) and **computations** that
   assign values when the page loads.
4. **Preview** (`.../pages/{pageId}/preview`) renders the page exactly as a
   runtime visitor sees it, including the items and region layout.

Save the page to persist regions, items, validations, processes and
computations through the builder API.

## 4. LOVs and REST data sources

- **Lists of values** (LOVs) define reusable option sets for select/radio items.
- **REST data sources** store remote endpoints that the app can call; they can be
  executed from the builder to inspect the response.

Both are reachable from the application builder screen.

## 5. Runtime

Each page has a runtime URL:

```
/api/v1/pages/{application_alias}/{page_number}
```

`GET` renders the page; submitting a form (`POST`) runs the page's validations
and processes, updates session state, and redirects back to the page (or to a
process-specified target). Rendered pages use the `miniui_session` cookie, and
form posts are exempt from the `X-Requested-With` CSRF header requirement because
a plain browser `<form>` cannot set custom headers.

## Concepts

| Concept | Meaning |
| --- | --- |
| Application | Top-level container; has a unique alias used in runtime URLs |
| Page | A screen inside an application, identified by number and alias |
| Region | A layout area on a page (form, report, static content, …) |
| Item | An input/display element inside a region |
| Validation | A rule that blocks submission and shows an error message |
| Process | Server-side logic at an execution point (e.g. after submit) |
| Computation | A value assigned to an item when the page renders |
| LOV | List of values backing select/radio options |
| REST data source | A stored external HTTP endpoint |

## Limits in this MVP

- Reports render result sets from a SQL query over session state; richer editable
  grids and charts are not implemented (see the stretch goals in
  `IMPLEMENTATION_PLAN.md`).
- Authentication is username/password with server-side sessions and account
  lockout; there is no self-service registration flow wired to the builder yet.
- There is no application export/import yet.
