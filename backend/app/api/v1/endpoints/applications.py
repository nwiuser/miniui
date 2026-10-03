"""
Application Endpoints
Handles HTTP requests for application management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .... import crud, schemas
from ....db import models
from ....core.auth import get_current_user, require_role, verify_application_access, get_current_session
from ....core.cache import application_metadata_cache
from ....db.session import get_db

router = APIRouter(
    prefix="/applications",
    tags=["applications"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Application])
def read_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Retrieve applications.
    Returns applications accessible to the current user:
    - ADMIN/DEVELOPER: All applications
    - END_USER: Only the application in their current session
    """
    # If user is ADMIN or DEVELOPER, they can see all applications
    if current_user.administrator_role in ["ADMIN", "DEVELOPER"]:
        applications = crud.get_applications(db, skip=skip, limit=limit)
    else:
        # END_USER can only see the application in their current session
        application = crud.get_application(db, application_id=current_session.application_id)
        applications = [application] if application else []
    return applications


@router.post("/", response_model=schemas.Application, status_code=status.HTTP_201_CREATED)
def create_application(application: schemas.ApplicationCreate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER"))):
    """
    Create new application.
    Only ADMIN and DEVELOPER roles can create applications.
    """
    return crud.create_application(db=db, application=application)


@router.get("/{application_id}", response_model=schemas.Application)
def read_application(application_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(verify_application_access)):
    """
    Get application by ID.
    """
    db_application = crud.get_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.put("/{application_id}", response_model=schemas.Application)
def update_application(application_id: int, application: schemas.ApplicationUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(verify_application_access)):
    """
    Update an application.
    Only ADMIN and DEVELOPER roles can update applications.
    """
    db_application = crud.update_application(db=db, application_id=application_id, application=application)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    application_metadata_cache.invalidate(application_id)
    return db_application


@router.delete("/{application_id}", response_model=schemas.Application)
def delete_application(application_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(verify_application_access)):
    """
    Delete an application.
    Only ADMIN role can delete applications.
    """
    db_application = crud.delete_application(db=db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    application_metadata_cache.invalidate(application_id)
    return db_application


def _build_application_metadata(db: Session, application_id: int) -> dict:
    """Assemble the full application definition as plain JSON-ready data.

    Returns ``None`` when the application does not exist. The result contains no
    ORM objects, which is what makes it safe to cache across requests.
    """
    application = crud.get_application(db, application_id=application_id)
    if application is None:
        return None

    def _column_dict(obj):
        if obj is None:
            return None
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    pages = db.query(models.Page).filter(
        models.Page.application_id == application_id
    ).order_by(models.Page.page_number).all()

    page_defs = []
    for page in pages:
        page_defs.append({
            **_column_dict(page),
            "regions": [
                _column_dict(r)
                for r in db.query(models.Region).filter(models.Region.page_id == page.id).all()
            ],
            "items": [
                _column_dict(i)
                for i in db.query(models.PageItem).filter(models.PageItem.page_id == page.id).all()
            ],
            "processes": [
                _column_dict(p)
                for p in db.query(models.PageProcess).filter(models.PageProcess.page_id == page.id).all()
            ],
            "computations": [
                _column_dict(c)
                for c in db.query(models.Computation).filter(models.Computation.page_id == page.id).all()
            ],
            "validations": [
                _column_dict(v)
                for v in db.query(models.Validation).filter(models.Validation.page_id == page.id).all()
            ],
        })

    return {"application": _column_dict(application), "pages": page_defs}


@router.get("/{application_id}/metadata", response_model=schemas.ApplicationMetadata)
def get_application_metadata(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER")),
):
    """
    Export a complete application definition (pages, regions, items, processes,
    computations, validations) as JSON for external consumption.

    Secured with the same authentication system; ADMIN/DEVELOPER only. The
    assembled definition is cached for a few seconds (``METADATA_CACHE_TTL``), so
    a heavy export does not hit the database on every poll. Edits may therefore
    take up to that TTL to show up here; the builder endpoints used for editing
    always read live data.
    """
    metadata = application_metadata_cache.get_or_set(
        application_id,
        lambda: _build_application_metadata(db, application_id),
    )
    if metadata is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return metadata