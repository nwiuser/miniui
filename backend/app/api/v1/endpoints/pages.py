"""
Page Endpoints
Handles HTTP requests for showing and accepting pages in the APEX-like application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, schemas
from ..db.session import get_db
from ....core.rendering.service import RenderingService
from ....core.session.service import SessionService


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

    Args:
        application_alias: The alias of the application
        page_number: The page number to show
        session_id: Optional session ID
        request: The FastAPI request object
        db: Database session

    Returns:
        HTML response with the rendered page
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

    Args:
        application_alias: The alias of the application
        page_number: The page number being submitted
        session_id: The session ID
        request: The FastAPI request object
        db: Database session

    Returns:
        JSON response with the result of processing the page
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