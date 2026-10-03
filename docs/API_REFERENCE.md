# API Reference

Generated from `backend/openapi.json` (Open Source APEX Equivalent v0.1.0). Do not edit by hand; regenerate with `scripts/generate_api_docs.py`.

## Authentication

Most endpoints require a session token obtained from `POST /api/v1/auth/login`. Two transports are accepted:

- `Authorization: Bearer <session_id>` header (used by the SPA/API clients).
- `miniui_session` HttpOnly cookie (set by login; used by rendered pages).

Mutating requests that are not form posts must also send `X-Requested-With: XMLHttpRequest` (CSRF protection). `/docs`, `/openapi.json`, the auth endpoints and runtime page posts are exempt.

Interactive documentation is served at `/docs` (Swagger UI) and `/redoc`.

## Endpoint Index

### applications

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/applications/` | Read Applications |
| POST | `/api/v1/applications/` | Create Application |
| GET | `/api/v1/applications/{application_id}` | Read Application |
| PUT | `/api/v1/applications/{application_id}` | Update Application |
| DELETE | `/api/v1/applications/{application_id}` | Delete Application |
| GET | `/api/v1/applications/{application_id}/metadata` | Get Application Metadata |

### auth

| Method | Path | Summary |
| --- | --- | --- |
| POST | `/api/v1/auth/change-password` | Change Password |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |

### computations

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/computations` | Get Computations |
| POST | `/api/v1/computations` | Create Computation |
| GET | `/api/v1/computations/{computation_id}` | Get Computation |
| PUT | `/api/v1/computations/{computation_id}` | Update Computation |
| DELETE | `/api/v1/computations/{computation_id}` | Delete Computation |

### default

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/` | Root |
| GET | `/api/` | Root |
| GET | `/health` | Health |

### items

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/items/` | Read Items |
| POST | `/api/v1/items/` | Create Item |
| GET | `/api/v1/items/{item_id}` | Read Item |
| PUT | `/api/v1/items/{item_id}` | Update Item |
| DELETE | `/api/v1/items/{item_id}` | Delete Item |

### lovs

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/lovs/` | Read Lovs |
| POST | `/api/v1/lovs/` | Create Lov |
| GET | `/api/v1/lovs/name/{lov_name}` | Read Lov By Name |
| GET | `/api/v1/lovs/{lov_id}` | Read Lov |
| PUT | `/api/v1/lovs/{lov_id}` | Update Lov |
| DELETE | `/api/v1/lovs/{lov_id}` | Delete Lov |

### pages

| Method | Path | Summary |
| --- | --- | --- |
| POST | `/api/v1/pages/builder/` | Create Page Builder |
| GET | `/api/v1/pages/builder/{application_id}` | Get Page Builder Context |
| PUT | `/api/v1/pages/builder/{page_id}` | Update Page Builder |
| DELETE | `/api/v1/pages/builder/{page_id}` | Delete Page Builder |
| GET | `/api/v1/pages/{application_alias}/{page_number}` | Show Page |
| POST | `/api/v1/pages/{application_alias}/{page_number}` | Accept Page |

### processes

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/processes` | Get Processes |
| POST | `/api/v1/processes` | Create Process |
| GET | `/api/v1/processes/{process_id}` | Get Process |
| PUT | `/api/v1/processes/{process_id}` | Update Process |
| DELETE | `/api/v1/processes/{process_id}` | Delete Process |

### regions

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/regions/` | Read Regions |
| POST | `/api/v1/regions/` | Create Region |
| GET | `/api/v1/regions/{region_id}` | Read Region |
| PUT | `/api/v1/regions/{region_id}` | Update Region |
| DELETE | `/api/v1/regions/{region_id}` | Delete Region |

### render

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/app/{appAlias}/{pageNumber}` | Render Page |

### rest-data-sources

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/rest-data-sources` | Get Rest Data Sources |
| POST | `/api/v1/rest-data-sources` | Create Rest Data Source |
| GET | `/api/v1/rest-data-sources/{source_id}` | Get Rest Data Source |
| PUT | `/api/v1/rest-data-sources/{source_id}` | Update Rest Data Source |
| DELETE | `/api/v1/rest-data-sources/{source_id}` | Delete Rest Data Source |
| POST | `/api/v1/rest-data-sources/{source_id}/execute` | Execute Rest Data Source |

### validations

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/validations/` | Read Validations |
| POST | `/api/v1/validations/` | Create Validation |
| GET | `/api/v1/validations/by-item/{page_id}/{item_name}` | Read Validations By Item |
| GET | `/api/v1/validations/by-page/{page_id}` | Read Validations By Page |
| GET | `/api/v1/validations/{validation_id}` | Read Validation |
| PUT | `/api/v1/validations/{validation_id}` | Update Validation |
| DELETE | `/api/v1/validations/{validation_id}` | Delete Validation |

### workspace-users

| Method | Path | Summary |
| --- | --- | --- |
| GET | `/api/v1/workspace-users/` | Read Workspace Users |
| POST | `/api/v1/workspace-users/` | Create Workspace User |
| GET | `/api/v1/workspace-users/username/{username}` | Read Workspace User By Username |
| GET | `/api/v1/workspace-users/{user_id}` | Read Workspace User |
| PUT | `/api/v1/workspace-users/{user_id}` | Update Workspace User |
| DELETE | `/api/v1/workspace-users/{user_id}` | Delete Workspace User |

## Endpoint Details

### applications

#### `GET /api/v1/applications/`

Read Applications

Retrieve applications.
Returns applications accessible to the current user:
- ADMIN/DEVELOPER: All applications
- END_USER: Only the application in their current session

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/applications/`

Create Application

Create new application.
Only ADMIN and DEVELOPER roles can create applications.

Request body (application/json, required): `ApplicationCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/applications/{application_id}`

Read Application

Get application by ID.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/applications/{application_id}`

Update Application

Update an application.
Only ADMIN and DEVELOPER roles can update applications.

Request body (application/json, required): `ApplicationUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/applications/{application_id}`

Delete Application

Delete an application.
Only ADMIN role can delete applications.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/applications/{application_id}/metadata`

Get Application Metadata

Export a complete application definition (pages, regions, items, processes,
computations, validations) as JSON for external consumption.

Secured with the same authentication system; ADMIN/DEVELOPER only. The
assembled definition is cached for a few seconds (``METADATA_CACHE_TTL``), so
a heavy export does not hit the database on every poll. Edits may therefore
take up to that TTL to show up here; the builder endpoints used for editing
always read live data.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### auth

#### `POST /api/v1/auth/change-password`

Change Password

Change the authenticated user's password.

Enforces the password strength policy and invalidates all other active
sessions for the user (the current session is preserved).

Request body (application/x-www-form-urlencoded, required): `Body_change_password_api_v1_auth_change_password_post`

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/auth/login`

Login

Login to get a session token (acting as access token in this MVP).

Request body (application/x-www-form-urlencoded, required): `Body_login_api_v1_auth_login_post`

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/auth/logout`

Logout

Log out user by invalidating the session.

Request body (application/x-www-form-urlencoded, required): `Body_logout_api_v1_auth_logout_post`

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### computations

#### `GET /api/v1/computations`

Get Computations

Retrieve computations. Optionally filter by page_id.
ADMIN/DEVELOPER: All computations. END_USER: Only those in their session's application.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `page_id` | query | no | integer | null |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

#### `POST /api/v1/computations`

Create Computation

Request body (application/json, required): `ComputationCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 422 | Validation Error |

#### `GET /api/v1/computations/{computation_id}`

Get Computation

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `computation_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

#### `PUT /api/v1/computations/{computation_id}`

Update Computation

Request body (application/json, required): `ComputationUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `computation_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

#### `DELETE /api/v1/computations/{computation_id}`

Delete Computation

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `computation_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 204 | Successful Response |
| 422 | Validation Error |

### default

#### `GET /`

Root

| Status | Description |
| --- | --- |
| 200 | Successful Response |

#### `GET /api/`

Root

| Status | Description |
| --- | --- |
| 200 | Successful Response |

#### `GET /health`

Health

Liveness probe used by Docker Compose and Kubernetes.

| Status | Description |
| --- | --- |
| 200 | Successful Response |

### items

#### `GET /api/v1/items/`

Read Items

Retrieve items. Optionally filter by page_id.
ADMIN/DEVELOPER: Can access all items
END_USER: Can only access items in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |
| `page_id` | query | no | integer | null |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/items/`

Create Item

Create a new item.
Only ADMIN and DEVELOPER roles can create items.

Request body (application/json, required): `ItemCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/items/{item_id}`

Read Item

Retrieve a specific item by ID.
ADMIN/DEVELOPER: Can access any item
END_USER: Can only access items in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `item_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/items/{item_id}`

Update Item

Update an existing item.
Only ADMIN and DEVELOPER roles can update items.

Request body (application/json, required): `ItemUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `item_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/items/{item_id}`

Delete Item

Delete an item.
Only ADMIN role can delete items.
END_USER can delete items only in their current session's application.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `item_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### lovs

#### `GET /api/v1/lovs/`

Read Lovs

Retrieve LOVs.
ADMIN/DEVELOPER: Can access all LOVs
END_USER: Can only access LOVs in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/lovs/`

Create Lov

Create new LOV.
ADMIN/DEVELOPER: Can create LOVs in any application
END_USER: Can only create LOVs in their current session's application

Request body (application/json, required): `LovCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/lovs/name/{lov_name}`

Read Lov By Name

Get LOV by name.
ADMIN/DEVELOPER: Can access any LOV
END_USER: Can only access LOVs from their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `lov_name` | path | yes | string |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/lovs/{lov_id}`

Read Lov

Get LOV by ID.
ADMIN/DEVELOPER: Can access any LOV
END_USER: Can only access LOVs from their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `lov_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/lovs/{lov_id}`

Update Lov

Update an LOV.
ADMIN/DEVELOPER: Can update any LOV
END_USER: Can only update LOVs in their current session's application

Request body (application/json, required): `LovUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `lov_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/lovs/{lov_id}`

Delete Lov

Delete a LOV.
Only ADMIN role can delete LOVs.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `lov_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### pages

#### `POST /api/v1/pages/builder/`

Create Page Builder

Create a new page (requires ADMIN or DEVELOPER role).

Request body (application/json, required): `PageCreate`

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/pages/builder/{application_id}`

Get Page Builder Context

Get context for the page builder (requires ADMIN or DEVELOPER role).
Returns pages and other metadata needed for the builder UI.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/pages/builder/{page_id}`

Update Page Builder

Update an existing page (requires ADMIN or DEVELOPER role).

Request body (application/json, required): `PageUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `page_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/pages/builder/{page_id}`

Delete Page Builder

Delete a page (requires ADMIN role).

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `page_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/pages/{application_alias}/{page_number}`

Show Page

Show a page by rendering it from metadata.

Public pages (``is_public=True``) render without authentication. Protected
pages require a valid session bound to the page's application.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_alias` | path | yes | string |  |
| `page_number` | path | yes | integer |  |
| `session_id` | query | no | string | null |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/pages/{application_alias}/{page_number}`

Accept Page

Accept a page submission (form post).

Requires a valid session for processing. Protected pages enforce the
session is bound to the page's application. ``p_session_id`` is accepted as
an alias of ``session_id`` for APEX-style form payloads.

Request body (application/x-www-form-urlencoded, optional): `Body_accept_page_api_v1_pages__application_alias___page_number__post`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_alias` | path | yes | string |  |
| `page_number` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### processes

#### `GET /api/v1/processes`

Get Processes

Retrieve processes. Optionally filter by page_id.
ADMIN/DEVELOPER: All processes. END_USER: Only processes in their session's application.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `page_id` | query | no | integer | null |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

#### `POST /api/v1/processes`

Create Process

Request body (application/json, required): `PageProcessCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 422 | Validation Error |

#### `GET /api/v1/processes/{process_id}`

Get Process

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `process_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

#### `PUT /api/v1/processes/{process_id}`

Update Process

Request body (application/json, required): `PageProcessUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `process_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

#### `DELETE /api/v1/processes/{process_id}`

Delete Process

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `process_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 204 | Successful Response |
| 422 | Validation Error |

### regions

#### `GET /api/v1/regions/`

Read Regions

Retrieve regions. Optionally filter by page_id.
ADMIN/DEVELOPER: Can access all regions
END_USER: Can only access regions in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |
| `page_id` | query | no | integer | null |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/regions/`

Create Region

Create a new region.
ADMIN/DEVELOPER: Can create regions in any application
END_USER: Can only create regions in their current session's application

Request body (application/json, required): `RegionCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/regions/{region_id}`

Read Region

Retrieve a specific region by ID.
ADMIN/DEVELOPER: Can access any region
END_USER: Can only access regions in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `region_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/regions/{region_id}`

Update Region

Update an existing region.
ADMIN/DEVELOPER: Can update any region
END_USER: Can only update regions in their current session's application

Request body (application/json, required): `RegionUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `region_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/regions/{region_id}`

Delete Region

Delete a region.
ADMIN: Can delete any region
DEVELOPER: Can delete any region (typically same as ADMIN for regions)
END_USER: Cannot delete regions (maintaining ADMIN-only restriction for delete, but with app access check)

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `region_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### render

#### `GET /api/v1/app/{appAlias}/{pageNumber}`

Render Page

Render a page as HTML based on application alias and page number.

Respects the page's public/protected visibility flag.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `appAlias` | path | yes | string |  |
| `pageNumber` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 422 | Validation Error |

### rest-data-sources

#### `GET /api/v1/rest-data-sources`

Get Rest Data Sources

Retrieve REST data sources.
ADMIN/DEVELOPER: All sources. END_USER: Only sources in their session's application.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `application_id` | query | no | integer | null |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/rest-data-sources`

Create Rest Data Source

Request body (application/json, required): `RestDataSourceCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/rest-data-sources/{source_id}`

Get Rest Data Source

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `source_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/rest-data-sources/{source_id}`

Update Rest Data Source

Request body (application/json, required): `RestDataSourceUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `source_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/rest-data-sources/{source_id}`

Delete Rest Data Source

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `source_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 204 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/rest-data-sources/{source_id}/execute`

Execute Rest Data Source

Execute a REST data source server-side and return the parsed response.

END_USER may only execute read-only (GET) sources within their session's
application. State-changing sources require ADMIN/DEVELOPER.

Request body (application/json, optional): `object | null`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `source_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### validations

#### `GET /api/v1/validations/`

Read Validations

Retrieve validations.
ADMIN/DEVELOPER: Can see all validations
END_USER: Can only see validations from their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/validations/`

Create Validation

Create new validation.
ADMIN/DEVELOPER: Can create validations in any application
END_USER: Can only create validations in their current session's application

Request body (application/json, required): `ValidationCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/validations/by-item/{page_id}/{item_name}`

Read Validations By Item

Retrieve validations for a specific item on a page.
ADMIN/DEVELOPER: Can access validations for any item
END_USER: Can only access validations for items in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `page_id` | path | yes | integer |  |
| `item_name` | path | yes | string |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/validations/by-page/{page_id}`

Read Validations By Page

Retrieve validations for a specific page.
ADMIN/DEVELOPER: Can access validations for any page
END_USER: Can only access validations for pages in their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `page_id` | path | yes | integer |  |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/validations/{validation_id}`

Read Validation

Get validation by ID.
ADMIN/DEVELOPER: Can access any validation
END_USER: Can only access validations from their current session's application

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `validation_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/validations/{validation_id}`

Update Validation

Update a validation.
ADMIN/DEVELOPER: Can update any validation
END_USER: Can only update validations in their current session's application

Request body (application/json, required): `ValidationUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `validation_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/validations/{validation_id}`

Delete Validation

Delete a validation.
ADMIN: Can delete any validation
END_USER: Cannot delete validations (maintaining ADMIN-only restriction, but with app access check)

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `validation_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

### workspace-users

#### `GET /api/v1/workspace-users/`

Read Workspace Users

Retrieve workspace users.
Only ADMIN role can list all users.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | no | integer |  |
| `limit` | query | no | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `POST /api/v1/workspace-users/`

Create Workspace User

Create new workspace user.
Only ADMIN role can create users.

Request body (application/json, required): `WorkspaceUserCreate`

| Status | Description |
| --- | --- |
| 201 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/workspace-users/username/{username}`

Read Workspace User By Username

Get workspace user by username.
Users can view their own profile, ADMIN can view any profile.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `username` | path | yes | string |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `GET /api/v1/workspace-users/{user_id}`

Read Workspace User

Get workspace user by ID.
Users can view their own profile, ADMIN can view any profile.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `PUT /api/v1/workspace-users/{user_id}`

Update Workspace User

Update a workspace user.
Users can update their own profile, ADMIN can update any profile.

Request body (application/json, required): `WorkspaceUserUpdate`

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |

#### `DELETE /api/v1/workspace-users/{user_id}`

Delete Workspace User

Delete a workspace user.
Only ADMIN role can delete users.

| Name | In | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | yes | integer |  |

| Status | Description |
| --- | --- |
| 200 | Successful Response |
| 404 | Not found |
| 422 | Validation Error |
