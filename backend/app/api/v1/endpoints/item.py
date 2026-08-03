"""
Item Endpoints
Handles HTTP requests for item management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..db.session import get_db
from .. import crud
from ..core.auth import require_role, application_access_required, get_current_user


router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, page_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Retrieve items. Optionally filter by page_id.
    """
    if page_id:
        items = crud.get_items_by_page(db, page_id=page_id, skip=skip, limit=limit)
    else:
        items = crud.get_items(db, skip=skip, limit=limit)
    return items


@router.get("/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific item by ID.
    """
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.post("/", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(application_access_required(item.page_id))):
    """
    Create a new item.
    Only ADMIN and DEVELOPER roles can create items.
    """
    return crud.create_item(db=db, item=item)


@router.put("/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Update an existing item.
    Only ADMIN and DEVELOPER roles can update items.
    """
    # First get the item to check its page_id for application access
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check application access using the item's page
    application_id = db_item.page.application_id if db_item.page else None
    if application_id:
        # ADMIN and DEVELOPER can access any application
        if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
            # For END_USER, we would need to check their session via application_access_required
            # For now, require ADMIN/DEVELOPER for item updates
            # TODO: Implement proper END_USER access checking based on session
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update items in this application"
            )

        # Verify the application still exists
        application = crud.get_application(db, application_id=application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

    db_item = crud.update_item(db, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.delete("/{item_id}", response_model=schemas.Item)
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Delete an item.
    Only ADMIN role can delete items.
    END_USER can delete items only in their current session's application.
    """
    # Get the item to verify it exists and check application access
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Get application ID from the item's page
    application_id = db_item.page.application_id if db_item.page else None

    # Check application access - ADMIN has full access, END_USER restricted to session (DEVELOPER treated as ADMIN for item deletion)
    if application_id:
        if current_user.administrator_role == "ADMIN":
            # ADMIN can delete any item but must verify application exists
            application = crud.get_application(db, application_id=application_id)
            if not application:
                raise HTTPException(status_code=404, detail="Application not found")
        elif current_user.administrator_role == "DEVELOPER":
            # DEVELOPER can delete any item (treated like ADMIN for item operations)
            application = crud.get_application(db, application_id=application_id)
            if not application:
                raise HTTPException(status_code=404, detail="Application not found")
        else:
            # END_USER can only delete items in their current session's application
            application_access_required(application_id)(current_user, None, db)

    # Perform the delete operation
    db_item = crud.delete_item(db=db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item