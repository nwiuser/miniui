"""
Page Endpoints
Handles HTTP requests for showing and accepting pages in the APEX-like application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from .... import schemas
from ....db import models
from ....db.session import get_db
from ....core.rendering.service import RenderingService
from ....core.session.service import SessionService
from ....core.auth import get_current_user, get_current_user_optional, require_role, application_access_required, get_current_application, verify_application_access
from .... import crud


router = APIRouter(
    prefix="/pages",
    tags=["pages"],
    responses={404: {"description": "Not found"}},
)


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
    Publicly accessible (no authentication required) for runtime viewing.
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

    # Create rendering service
    rendering_service = RenderingService(db)

    # Show the page
    result = rendering_service.show_page(
        application_alias=application_alias,
        page_number=page_number,
        session_id=session_id,
        request=request
    )

    # Return the HTML
    return HTMLResponse(content=result["html"])


@router.post("/{application_alias}/{page_number}")
async def accept_page(
    application_alias: str,
    page_number: int,
    session_id: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Accept a page submission (form post).
    Requires valid session for processing.
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

    # Get form data from the request
    form = await request.form()
    form_data = dict(form)

    # Create rendering service
    rendering_service = RenderingService(db)

    # Accept the page
    result = rendering_service.accept_page(
        application_alias=application_alias,
        page_number=page_number,
        session_id=session_id,
        form_data=form_data
    )

    # If there was a redirect URL, return a redirect response
    if result.get("success") and result.get("redirect_url"):
        return RedirectResponse(url=result["redirect_url"], status_code=303)

    # Otherwise, return JSON result
    return result


# Builder endpoints - require authentication and appropriate roles
@router.get("/builder/{application_id}")
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


@router.post("/builder/", response_model=schemas.Page)
def create_page_builder(
    page: schemas.PageCreate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    """
    Create a new page (requires ADMIN or DEVELOPER role).
    """
    # A dependency cannot read a body sub-field, so enforce per-application
    # access for the page's application_id here (matches existing manual checks).
    application_access_required(page.application_id)(current_user, None, db)
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