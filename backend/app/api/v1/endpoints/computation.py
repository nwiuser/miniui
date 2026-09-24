from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import schemas
from ....db import models
from ....db.session import get_db
from ....core.auth import get_current_user, require_role, get_current_session, application_access_required


router = APIRouter()


def _check_computation_access(db: Session, computation: models.Computation, current_user, current_session) -> None:
    """Enforce application-scoped access for a computation via its page."""
    if not computation.page:
        raise HTTPException(status_code=404, detail="Computation belongs to no page")
    application_access_required(computation.page.application_id)(current_user, current_session, db)


@router.get("", response_model=List[schemas.Computation])
def get_computations(
    page_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    """
    Retrieve computations. Optionally filter by page_id.
    ADMIN/DEVELOPER: All computations. END_USER: Only those in their session's application.
    """
    if page_id:
        page = db.query(models.Page).filter(models.Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        application_access_required(page.application_id)(current_user, current_session, db)

    query = db.query(models.Computation)

    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        query = query.join(models.Page).filter(
            models.Page.application_id == current_session.application_id
        )

    if page_id:
        query = query.filter(models.Computation.page_id == page_id)
    return query.order_by(models.Computation.sequence).all()


@router.get("/{computation_id}", response_model=schemas.Computation)
def get_computation(
    computation_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    computation = db.query(models.Computation).filter(models.Computation.id == computation_id).first()
    if not computation:
        raise HTTPException(status_code=404, detail="Computation not found")
    _check_computation_access(db, computation, current_user, current_session)
    return computation


@router.post("", response_model=schemas.Computation, status_code=status.HTTP_201_CREATED)
def create_computation(
    computation: schemas.ComputationCreate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    page = db.query(models.Page).filter(models.Page.id == computation.page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    application_access_required(page.application_id)(current_user, current_session, db)

    db_computation = models.Computation(**computation.model_dump())
    db.add(db_computation)
    db.commit()
    db.refresh(db_computation)
    return db_computation


@router.put("/{computation_id}", response_model=schemas.Computation)
def update_computation(
    computation_id: int,
    computation: schemas.ComputationUpdate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    db_computation = db.query(models.Computation).filter(models.Computation.id == computation_id).first()
    if not db_computation:
        raise HTTPException(status_code=404, detail="Computation not found")
    _check_computation_access(db, db_computation, current_user, current_session)

    update_data = computation.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_computation, key, value)

    db.commit()
    db.refresh(db_computation)
    return db_computation


@router.delete("/{computation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_computation(
    computation_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session)
):
    if current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can delete computations"
        )
    db_computation = db.query(models.Computation).filter(models.Computation.id == computation_id).first()
    if not db_computation:
        raise HTTPException(status_code=404, detail="Computation not found")
    _check_computation_access(db, db_computation, current_user, current_session)

    db.delete(db_computation)
    db.commit()