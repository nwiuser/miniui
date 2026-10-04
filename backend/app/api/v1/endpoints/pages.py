"""
Page Endpoints
Handles HTTP requests for showing and accepting pages in the APEX-like application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
import os
import json
from .... import schemas
from ....db import models
from ....db.session import get_db
from ....core.rendering.service import RenderingService
from ....core.session.service import SessionService
from ....core.auth import get_current_user, get_current_user_optional, require_role, application_access_required, get_current_application, get_current_session, verify_application_access
from .... import crud


router = APIRouter(
    prefix="/pages",
    tags=["pages"],
    responses={404: {"description": "Not found"}},
)


SESSION_COOKIE = "miniui_session"


def _cookie_secure() -> bool:
    """Secure flag for session cookie (enable over HTTPS in production)."""
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"


def _resolve_session_id(request: Request, explicit: Optional[str]) -> Optional[str]:
    """Prefer an explicitly supplied session ID, else fall back to the session cookie."""
    return explicit or request.cookies.get(SESSION_COOKIE)


def _set_session_cookie(response: Response, session_id: str) -> None:
    """Store the session ID in an HttpOnly, SameSite cookie."""
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        max_age=24 * 60 * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
    )


def _validate_page_session(
    db: Session,
    session_id: Optional[str],
    page: models.Page,
) -> models.Session:
    """
    Validate that a session can view a page.

    Protected pages require a valid, active session bound to the page's
    application. Public pages may be viewed without a session (returns None
    for anonymous viewing).
    """
    if page.is_public:
        if not session_id:
            return None
        return _get_session_for_page(db, session_id, page)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view this page",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _get_session_for_page(db, session_id, page)


def _get_session_for_page(db: Session, session_id: str, page: models.Page) -> Optional[models.Session]:
    """Return the session if valid and bound to the page's application."""
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if session.application_id != page.application_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this page"
        )
    return session


@router.get(
    "/builder/{application_id}",
    dependencies=[Depends(require_role("ADMIN", "DEVELOPER"))],
)
def get_page_builder_context(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(verify_application_access)
):
    """
    Get context for the page builder (requires ADMIN or DEVELOPER role).
    Returns pages and other metadata needed for the builder UI.
    """
    # Verify application exists
    application = crud.get_application(db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get pages for this application
    pages = crud.get_pages_by_application(db, application_id=application_id)

    return {
        "application": application,
        "pages": pages
    }


@router.get(
    "/builder/page/{page_id}",
    response_model=schemas.Page,
)
def get_page_builder(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
):
    """
    Get a single page for the visual builder (requires ADMIN or DEVELOPER).

    This is separate from ``GET /builder/{application_id}`` (which returns the
    whole builder context for an application) so a page id is never mistaken
    for an application id.
    """
    db_page = crud.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    application = crud.get_application(db, application_id=db_page.application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return db_page


@router.post("/builder/", response_model=schemas.Page)
def create_page_builder(
    page: schemas.PageCreate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER")),
    current_session: models.Session = Depends(get_current_session),
):
    """
    Create a new page (requires ADMIN or DEVELOPER role).
    """
    # A dependency cannot read a body sub-field, so enforce per-application
    # access for the page's application_id here (matches existing manual checks).
    application_access_required(page.application_id)(current_user, current_session, db)
    return crud.create_page(db=db, page=page)


@router.put("/builder/{page_id}", response_model=schemas.Page)
def update_page_builder(
    page_id: int,
    page: schemas.PageUpdate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    """
    Update an existing page (requires ADMIN or DEVELOPER role).
    """
    # Get the page to verify application access
    db_page = crud.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check application access
    application_id = db_page.application_id
    # ADMIN/DEVELOPER only; verify the application still exists
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Verify application exists
    application = crud.get_application(db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db_page = crud.update_page(db=db, page_id=page_id, page=page)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return db_page


@router.delete("/builder/{page_id}", response_model=schemas.Page)
def delete_page_builder(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    """
    Delete a page (requires ADMIN role).
    """
    # Get the page to verify application access
    db_page = crud.get_page(db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check application access
    application_id = db_page.application_id

    # Only ADMIN can delete pages
    if current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Verify application exists
    application = crud.get_application(db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db_page = crud.delete_page(db=db, page_id=page_id)
    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return db_page


# Runtime routes. These are declared after the builder routes on purpose:
# "/builder/{application_id}" would otherwise be swallowed by
# "/{application_alias}/{page_number}" and answer with "application 'builder'
# not found", leaving the builder unable to load its context.
@router.get("/{application_alias}/{page_number}", response_class=HTMLResponse)
async def show_page(
    application_alias: str,
    page_number: int,
    session_id: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Show a page by rendering it from metadata.

    Public pages (``is_public=True``) render without authentication. Protected
    pages require a valid session bound to the page's application.
    """
    # Get the application by alias
    application = db.query(models.Application).filter(
        models.Application.alias == application_alias,
        models.Application.is_active == True
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application with alias '{application_alias}' not found"
        )

    # Get page by application ID and page number
    page = db.query(models.Page).filter(
        models.Page.application_id == application.id,
        models.Page.page_number == page_number,
        models.Page.is_active == True
    ).first()

    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_number} not found in application '{application_alias}'"
        )

    # Resolve the session (explicit param or cookie) and enforce public/protected
    resolved_session_id = _resolve_session_id(request, session_id)
    _validate_page_session(db, resolved_session_id, page)

    # Create rendering service
    rendering_service = RenderingService(db)

    # Show the page
    result = rendering_service.show_page(
        application_alias=application_alias,
        page_number=page_number,
        session_id=resolved_session_id,
        request=request
    )

    # Return the HTML and persist the session cookie. Rendered fresh from
    # metadata on every request, so forbid caching: the builder's standalone
    # view must show the latest saved state without a manual refresh.
    response = HTMLResponse(content=result["html"])
    response.headers["Cache-Control"] = "no-store, max-age=0"
    session_cookie = result.get("session_id") or resolved_session_id
    if session_cookie:
        _set_session_cookie(response, session_cookie)
    return response


@router.post("/{application_alias}/{page_number}")
async def accept_page(
    application_alias: str,
    page_number: int,
    session_id: Optional[str] = Form(None),
    p_session_id: Optional[str] = Form(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Accept a page submission (form post).

    Requires a valid session for processing. Protected pages enforce the
    session is bound to the page's application. ``p_session_id`` is accepted as
    an alias of ``session_id`` for APEX-style form payloads.
    """
    # Get the application by alias
    application = db.query(models.Application).filter(
        models.Application.alias == application_alias,
        models.Application.is_active == True
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application with alias '{application_alias}' not found"
        )

    # Get page by application ID and page number
    page = db.query(models.Page).filter(
        models.Page.application_id == application.id,
        models.Page.page_number == page_number,
        models.Page.is_active == True
    ).first()

    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_number} not found in application '{application_alias}'"
        )

# Resolve the session (form field or cookie) and enforce public/protected
    resolved_session_id = _resolve_session_id(request, session_id or p_session_id)
    _validate_page_session(db, resolved_session_id, page)

    # Get form data from the request
    form = await request.form()
    form_data = {
        key: value
        for key, value in form.items()
        if key not in {"session_id", "p_session_id"}
    }

    # Create rendering service
    rendering_service = RenderingService(db)

    # Accept the page
    result = rendering_service.accept_page(
        application_alias=application_alias,
        page_number=page_number,
        session_id=resolved_session_id,
        form_data=form_data
    )

    # If there was a redirect URL, return a redirect response
    if result.get("success") and result.get("redirect_url"):
        response = RedirectResponse(url=result["redirect_url"], status_code=303)
        if resolved_session_id:
            _set_session_cookie(response, resolved_session_id)
        return response

    # Otherwise, return JSON result
    response = Response(
        content=json.dumps(result),
        media_type="application/json",
    )
    if resolved_session_id:
        _set_session_cookie(response, resolved_session_id)
    return response
