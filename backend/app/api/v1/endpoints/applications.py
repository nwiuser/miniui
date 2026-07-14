from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..db.session import get_db

router = APIRouter(
    prefix="/applications",
    tags=["applications"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Application])
def read_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve applications.
    """
    applications = crud.get_applications(db, skip=skip, limit=limit)
    return applications


@router.post("/", response_model=schemas.Application, status_code=status.HTTP_201_CREATED)
def create_application(application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    """
    Create new application.
    """
    return crud.create_application(db=db, application=application)


@router.get("/{application_id}", response_model=schemas.Application)
def read_application(application_id: int, db: Session = Depends(get_db)):
    """
    Get application by ID.
    """
    db_application = crud.get_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.put("/{application_id}", response_model=schemas.Application)
def update_application(application_id: int, application: schemas.ApplicationUpdate, db: Session = Depends(get_db)):
    """
    Update an application.
    """
    db_application = crud.update_application(db=db, application_id=application_id, application=application)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.delete("/{application_id}", response_model=schemas.Application)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """
    Delete an application.
    """
    db_application = crud.delete_application(db=db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application