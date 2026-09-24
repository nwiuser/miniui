from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import schemas
from ....db import models
from ....db.session import get_db
from ....core.auth import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=List[schemas.PageProcess])
def get_processes(
    page_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    query = db.query(models.PageProcess)
    if page_id:
        query = query.filter(models.PageProcess.page_id == page_id)
    return query.order_by(models.PageProcess.execution_sequence).all()


@router.get("/{process_id}", response_model=schemas.PageProcess)
def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user)
):
    process = db.query(models.PageProcess).filter(models.PageProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.post("", response_model=schemas.PageProcess, status_code=status.HTTP_201_CREATED)
def create_process(
    process: schemas.PageProcessCreate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER"))
):
    db_process = models.PageProcess(**process.model_dump())
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return db_process


@router.put("/{process_id}", response_model=schemas.PageProcess)
def update_process(
    process_id: int,
    process: schemas.PageProcessUpdate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN", "DEVELOPER"))
):
    db_process = db.query(models.PageProcess).filter(models.PageProcess.id == process_id).first()
    if not db_process:
        raise HTTPException(status_code=404, detail="Process not found")

    update_data = process.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_process, key, value)

    db.commit()
    db.refresh(db_process)
    return db_process


@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(require_role("ADMIN"))
):
    db_process = db.query(models.PageProcess).filter(models.PageProcess.id == process_id).first()
    if not db_process:
        raise HTTPException(status_code=404, detail="Process not found")

    db.delete(db_process)
    db.commit()
