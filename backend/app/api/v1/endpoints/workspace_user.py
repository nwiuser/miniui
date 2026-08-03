"""
Workspace User Endpoints
Handles HTTP requests for workspace user management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..db.session import get_db
from .. import crud
from ..core.auth import get_current_user, require_role


router = APIRouter(
    prefix="/workspace-users",
    tags=["workspace-users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.WorkspaceUser])
def read_workspace_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(require_role("ADMIN"))):
    """
    Retrieve workspace users.
    Only ADMIN role can list all users.
    """
    users = crud.get_workspace_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=schemas.WorkspaceUser, status_code=status.HTTP_201_CREATED)
def create_workspace_user(user: schemas.WorkspaceUserCreate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(require_role("ADMIN"))):
    """
    Create new workspace user.
    Only ADMIN role can create users.
    """
    return crud.create_workspace_user(db=db, user=user)


@router.get("/{user_id}", response_model=schemas.WorkspaceUser)
def read_workspace_user(user_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Get workspace user by ID.
    Users can view their own profile, ADMIN can view any profile.
    """
    db_user = crud.get_workspace_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Users can only view their own profile unless they are ADMIN
    if current_user.id != user_id and current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's information"
        )
    return db_user


@router.get("/username/{username}", response_model=schemas.WorkspaceUser)
def read_workspace_user_by_username(username: str, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Get workspace user by username.
    Users can view their own profile, ADMIN can view any profile.
    """
    db_user = crud.get_workspace_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Users can only view their own profile unless they are ADMIN
    if current_user.id != db_user.id and current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's information"
        )
    return db_user


@router.put("/{user_id}", response_model=schemas.WorkspaceUser)
def update_workspace_user(user_id: int, user: schemas.WorkspaceUserUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Update a workspace user.
    Users can update their own profile, ADMIN can update any profile.
    """
    # Only allow users to update their own profile unless they are ADMIN
    if current_user.id != user_id and current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    db_user = crud.update_workspace_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}", response_model=schemas.WorkspaceUser)
def delete_workspace_user(user_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(require_role("ADMIN"))):
    """
    Delete a workspace user.
    Only ADMIN role can delete users.
    """
    db_user = crud.delete_workspace_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user