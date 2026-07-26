from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..db.session import get_db

router = APIRouter(
    prefix="/validations",
    tags=["validations"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Validation])
def read_validations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve validations.
    """
    validations = crud.get_validations(db, skip=skip, limit=limit)
    return validations


@router.get("/by-page/{page_id}", response_model=List[schemas.Validation])
def read_validations_by_page(page_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve validations for a specific page.
    """
    validations = crud.get_validations_by_page(db, page_id=page_id, skip=skip, limit=limit)
    return validations


@router.get("/by-item/{page_id}/{item_name}", response_model=List[schemas.Validation])
def read_validations_by_item(page_id: int, item_name: str, db: Session = Depends(get_db)):
    """
    Retrieve validations for a specific item on a page.
    """
    validations = crud.get_validations_by_item(db, page_id=page_id, item_name=item_name)
    return validations


@router.post("/", response_model=schemas.Validation, status_code=status.HTTP_201_CREATED)
def create_validation(validation: schemas.ValidationCreate, db: Session = Depends(get_db)):
    """
    Create new validation.
    """
    return crud.create_validation(db=db, validation=validation)


@router.get("/{validation_id}", response_model=schemas.Validation)
def read_validation(validation_id: int, db: Session = Depends(get_db)):
    """
    Get validation by ID.
    """
    db_validation = crud.get_validation(db, validation_id=validation_id)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return db_validation


@router.put("/{validation_id}", response_model=schemas.Validation)
def update_validation(validation_id: int, validation: schemas.ValidationUpdate, db: Session = Depends(get_db)):
    """
    Update a validation.
    """
    db_validation = crud.update_validation(db=db, validation_id=validation_id, validation=validation)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return db_validation


@router.delete("/{validation_id}", response_model=schemas.Validation)
def delete_validation(validation_id: int, db: Session = Depends(get_db)):
    """
    Delete a validation.
    """
    db_validation = crud.delete_validation(db=db, validation_id=validation_id)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return db_validation