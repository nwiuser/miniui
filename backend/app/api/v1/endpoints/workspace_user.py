from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..db.session import get_db

router = APIRouter(
    prefix="/workspace-users",
    tags=["workspace-users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.WorkspaceUser])
def read_workspace_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve workspace users.
    """
    users = crud.get_workspace_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=schemas.WorkspaceUser, status_code=status.HTTP_201_CREATED)
def create_workspace_user(user: schemas.WorkspaceUserCreate, db: Session = Depends(get_db)):
    """
    Create new workspace user.
    """
    return crud.create_workspace_user(db=db, user=user)


@router.get("/{user_id}", response_model=schemas.WorkspaceUser)
def read_workspace_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get workspace user by ID.
    """
    db_user = crud.get_workspace_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/username/{username}", response_model=schemas.WorkspaceUser)
def read_workspace_user_by_username(username: str, db: Session = Depends(get_db)):
    """
    Get workspace user by username.
    """
    db_user = crud.get_workspace_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.WorkspaceUser)
def update_workspace_user(user_id: int, user: schemas.WorkspaceUserUpdate, db: Session = Depends(get_db)):
    """
    Update a workspace user.
    """
    db_user = crud.update_workspace_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}", response_model=schemas.WorkspaceUser)
def delete_workspace_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a workspace user.
    """
    db_user = crud.delete_workspace_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user