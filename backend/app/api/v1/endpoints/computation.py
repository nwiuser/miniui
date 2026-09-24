from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ....db import models
from ....db.session import get_db
from ....core.auth import get_current_user, require_role


router = APIRouter()


@router.get("", response_model=List[dict])
def get_computations(
    page_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    query = db.query(models.Computation)
    if page_id:
        query = query.filter(models.Computation.page_id == page_id)
    return query.order_by(models.Computation.sequence).all()


@router.get("/{computation_id}")
def get_computation(
    computation_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    computation = db.query(models.Computation).filter(models.Computation.id == computation_id).first()
    if not computation:
        raise HTTPException(status_code=404, detail="Computation not found")
    return computation


@router.post("", status_code=status.HTTP_201_CREATED)
def create_computation(
    computation: dict,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER"))
):
    db_computation = models.Computation(**computation)
    db.add(db_computation)
    db.commit()
    db.refresh(db_computation)
    return db_computation


@router.put("/{computation_id}")
def update_computation(
    computation_id: int,
    computation: dict,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER"))
):
    db_computation = db.query(models.Computation).filter(models.Computation.id == computation_id).first()
    if not db_computation:
        raise HTTPException(status_code=404, detail="Computation not found")

    for key, value in computation.items():
        if key != "id":
            setattr(db_computation, key, value)

    db.commit()
    db.refresh(db_computation)
    return db_computation


@router.delete("/{computation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_computation(
    computation_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN"))
):
    db_computation = db.query(models.Computation).filter(models.Computation.id == computation_id).first()
    if not db_computation:
        raise HTTPException(status_code=404, detail="Computation not found")

    db.delete(db_computation)
    db.commit()
