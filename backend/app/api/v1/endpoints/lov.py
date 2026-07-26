from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..db.session import get_db

router = APIRouter(
    prefix="/lovs",
    tags=["lovs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Lov])
def read_lovs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve LOVs.
    """
    lovs = crud.get_lovs(db, skip=skip, limit=limit)
    return lovs


@router.post("/", response_model=schemas.Lov, status_code=status.HTTP_201_CREATED)
def create_lov(lov: schemas.LovCreate, db: Session = Depends(get_db)):
    """
    Create new LOV.
    """
    return crud.create_lov(db=db, lov=lov)


@router.get("/{lov_id}", response_model=schemas.Lov)
def read_lov(lov_id: int, db: Session = Depends(get_db)):
    """
    Get LOV by ID.
    """
    db_lov = crud.get_lov(db, lov_id=lov_id)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")
    return db_lov


@router.get("/name/{lov_name}", response_model=schemas.Lov)
def read_lov_by_name(lov_name: str, db: Session = Depends(get_db)):
    """
    Get LOV by name.
    """
    db_lov = crud.get_lov_by_name(db, lov_name=lov_name)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")
    return db_lov


@router.put("/{lov_id}", response_model=schemas.Lov)
def update_lov(lov_id: int, lov: schemas.LovUpdate, db: Session = Depends(get_db)):
    """
    Update an LOV.
    """
    db_lov = crud.update_lov(db=db, lov_id=lov_id, lov=lov)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")
    return db_lov


@router.delete("/{lov_id}", response_model=schemas.Lov)
def delete_lov(lov_id: int, db: Session = Depends(get_db)):
    """
    Delete an LOV.
    """
    db_lov = crud.delete_lov(db=db, lov_id=lov_id)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")
    return db_lov