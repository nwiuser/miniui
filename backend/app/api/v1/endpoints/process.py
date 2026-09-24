from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import schemas
from ....db import models
from ....db.session import get_db
from ....core.auth import get_current_user, require_role, get_current_session, application_access_required

router = APIRouter()


def _check_process_access(db: Session, process: models.PageProcess, current_user, current_session) -> None:
    """Enforce application-scoped access for a process via its page."""
    if not process.page:
        raise HTTPException(status_code=404, detail="Process belongs to no page")
    application_access_required(process.page.application_id)(current_user, current_session, db)


@router.get("", response_model=List[schemas.PageProcess])
def get_processes(
    page_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    """
    Retrieve processes. Optionally filter by page_id.
    ADMIN/DEVELOPER: All processes. END_USER: Only processes in their session's application.
    """
    if page_id:
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        application_access_required(page.application_id)(current_user, current_session, db)

    query = db.query(models.PageProcess)

    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        query = query.join(models.Page).filter(
            models.Page.application_id == current_session.application_id
        )

    if page_id:
        query = query.filter(models.PageProcess.page_id == page_id)
    return query.order_by(models.PageProcess.execution_sequence).all()


@router.get("/{process_id}", response_model=schemas.PageProcess)
def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    process = db.query(models.PageProcess).filter(models.PageProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    _check_process_access(db, process, current_user, current_session)
    return process


@router.post("", response_model=schemas.PageProcess, status_code=status.HTTP_201_CREATED)
def create_process(
    process: schemas.PageProcessCreate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    page = db.query(models.Page).filter(models.Page.id == process.page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    application_access_required(page.application_id)(current_user, current_session, db)

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
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    db_process = db.query(models.PageProcess).filter(models.PageProcess.id == process_id).first()
    if not db_process:
        raise HTTPException(status_code=404, detail="Process not found")
    _check_process_access(db, db_process, current_user, current_session)

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
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    if current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can delete processes"
        )
    db_process = db.query(models.PageProcess).filter(models.PageProcess.id == process_id).first()
    if not db_process:
        raise HTTPException(status_code=404, detail="Process not found")
    _check_process_access(db, db_process, current_user, current_session)

    db.delete(db_process)
    db.commit()