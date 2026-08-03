"""
Application Endpoints
Handles HTTP requests for application management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..core.auth import get_current_user, require_role, application_access_required
from ..db.session import get_db

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
def read_application(application_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(application_access_required(application_id))):
    """
    Get application by ID.
    """
    db_application = crud.get_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.put("/{application_id}", response_model=schemas.Application)
def update_application(application_id: int, application: schemas.ApplicationUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(application_access_required(application_id))):
    """
    Update an application.
    Only ADMIN and DEVELOPER roles can update applications.
    """
    db_application = crud.update_application(db=db, application_id=application_id, application=application)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.delete("/{application_id}", response_model=schemas.Application)
def delete_application(application_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(application_access_required(application_id))):
    """
    Delete an application.
    Only ADMIN role can delete applications.
    """
    db_application = crud.delete_application(db=db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application