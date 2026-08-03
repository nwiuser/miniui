"""
LOV Endpoints
Handles HTTP requests for LOV management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..db.session import get_db
from .. import crud
from ..core.auth import require_role, application_access_required, get_current_user


router = APIRouter(
    prefix="/lovs",
    tags=["lovs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Lov])
def read_lovs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Retrieve LOVs.
    ADMIN/DEVELOPER: Can access all LOVs
    END_USER: Can only access LOVs in their current session's application
    """
    # For ADMIN/DEVELOPER, show all
    if current_user.administrator_role in ["ADMIN", "DEVELOPER"]:
        lovs = crud.get_lovs(db, skip=skip, limit=limit)
    else:
        # END_USER: get LOVs only from their current session's application
        if current_user.session_id:
            from .. import crud
            session = crud.get_session(db, session_id=current_user.session_id)
            if session and session.application_id:
                lovs = crud.get_lovs_by_application(db, application_id=session.application_id, skip=skip, limit=limit)
            else:
                lovs = []  # No active session, no access
        else:
            lovs = []  # No session, no access

    return lovs


@router.post("/", response_model=schemas.Lov, status_code=status.HTTP_201_CREATED)
def create_lov(lov: schemas.LovCreate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Create new LOV.
    ADMIN/DEVELOPER: Can create LOVs in any application
    END_USER: Can only create LOVs in their current session's application
    """
    # Check if LOV specifies an item_id
    if hasattr(lov, 'item_id') and lov.item_id:
        from .. import crud
        item = crud.get_item(db, item_id=lov.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if item.page:
            application_id = item.page.application_id
            application_access_required(application_id)(current_user, None, db)
    # If no item_id, it's a global LOV - ADMIN/DEVELOPER can create, END_USER would need special handling
    # For now, we'll allow ADMIN/DEVELOPER and restrict END_USER (they'd need to specify item_id)

    return crud.create_lov(db=db, lov=lov)


@router.get("/{lov_id}", response_model=schemas.Lov)
def read_lov(lov_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Get LOV by ID.
    ADMIN/DEVELOPER: Can access any LOV
    END_USER: Can only access LOVs from their current session's application
    """
    db_lov = crud.get_lov(db, lov_id=lov_id)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")

    # Note: LOVs don't have direct application relationship in current schema
    # They might be associated with items or be global
    # For now, we'll allow ADMIN/DEVELOPER access and check if there's an indirect application link
    # This would need to be adjusted based on actual LOV-to-application relationship

    # If LOV has an item_id, check through item->page->application
    if hasattr(db_lov, 'item_id') and db_lov.item_id:
        from .. import crud
        item = crud.get_item(db, item_id=db_lov.item_id)
        if item and item.page:
            application_id = item.page.application_id
            application_access_required(application_id)(current_user, None, db)

    return db_lov


@router.get("/name/{lov_name}", response_model=schemas.Lov)
def read_lov_by_name(lov_name: str, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Get LOV by name.
    ADMIN/DEVELOPER: Can access any LOV
    END_USER: Can only access LOVs from their current session's application
    """
    db_lov = crud.get_lov_by_name(db, lov_name=lov_name)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")

    # Apply same application access logic as get_lov
    # If LOV has an item_id, check through item->page->application
    if hasattr(db_lov, 'item_id') and db_lov.item_id:
        from .. import crud
        item = crud.get_item(db, item_id=db_lov.item_id)
        if item and item.page:
            application_id = item.page.application_id
            application_access_required(application_id)(current_user, None, db)

    return db_lov


@router.put("/{lov_id}", response_model=schemas.Lov)
def update_lov(lov_id: int, lov: schemas.LovUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Update an LOV.
    ADMIN/DEVELOPER: Can update any LOV
    END_USER: Can only update LOVs in their current session's application
    """
    db_lov = crud.get_lov(db, lov_id=lov_id)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")

    # Apply application access check if LOV has item association
    if hasattr(db_lov, 'item_id') and db_lov.item_id:
        from .. import crud
        item = crud.get_item(db, item_id=db_lov.item_id)
        if item and item.page:
            application_id = item.page.application_id
            application_access_required(application_id)(current_user, None, db)

    db_lov = crud.update_lov(db=db, lov_id=lov_id, lov=lov)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")
    return db_lov


@router.delete("/{lov_id}", response_model=schemas.Lov)
def delete_lov(lov_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(require_role("ADMIN"))):
    """
    Delete a LOV.
    Only ADMIN role can delete LOVs.
    """
    db_lov = crud.delete_lov(db=db, lov_id=lov_id)
    if db_lov is None:
        raise HTTPException(status_code=404, detail="LOV not found")
    return db_lov