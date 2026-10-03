"""
Validation Endpoints
Handles HTTP requests for validation management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .... import schemas
from ....db import models
from ....db.session import get_db
from .... import crud
from ....core.auth import require_role, application_access_required, get_current_user, get_current_session


router = APIRouter(
    prefix="/validations",
    tags=["validations"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Validation])
def read_validations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Retrieve validations.
    ADMIN/DEVELOPER: Can see all validations
    END_USER: Can only see validations from their current session's application
    """
    # For END_USER, we need to filter by their application
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        # END_USER - get application from their session
        from .... import crud
        session = crud.get_session_by_user_and_app(db, user_id=current_user.id, is_active=True)  # Simplified
        if not session or not session.application_id:
            return []  # No active session, no access
        application_id = session.application_id
        validations = crud.get_validations_by_application(db, application_id=application_id, skip=skip, limit=limit)
    else:
        # ADMIN/DEVELOPER - get all
        validations = crud.get_validations(db, skip=skip, limit=limit)
    return validations


@router.get("/by-page/{page_id}", response_model=List[schemas.Validation])
def read_validations_by_page(page_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Retrieve validations for a specific page.
    ADMIN/DEVELOPER: Can access validations for any page
    END_USER: Can only access validations for pages in their current session's application
    """
    # Get the page to check its application
    page = crud.get_page(db, page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check application access
    application_id = page.application_id
    application_access_required(application_id)(current_user, current_session, db)

    # Get validations for this page
    validations = crud.get_validations_by_page(db, page_id=page_id, skip=skip, limit=limit)
    return validations


@router.get("/by-item/{page_id}/{item_name}", response_model=List[schemas.Validation])
def read_validations_by_item(page_id: int, item_name: str, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Retrieve validations for a specific item on a page.
    ADMIN/DEVELOPER: Can access validations for any item
    END_USER: Can only access validations for items in their current session's application
    """
    # Get the page to check its application
    page = crud.get_page(db, page_id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check application access
    application_id = page.application_id
    application_access_required(application_id)(current_user, current_session, db)

    # Get validations for this item
    validations = crud.get_validations_by_item(db, page_id=page_id, item_name=item_name)
    return validations


@router.get("/{validation_id}", response_model=schemas.Validation)
def read_validation(validation_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Get validation by ID.
    ADMIN/DEVELOPER: Can access any validation
    END_USER: Can only access validations from their current session's application
    """
    # Get the validation to check its application
    db_validation = crud.get_validation(db, validation_id=validation_id)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Get the application through validation -> page -> application
    application_id = db_validation.page.application_id if db_validation.page else None

    if application_id:
        # Check application access
        application_access_required(application_id)(current_user, current_session, db)

    return db_validation


@router.post("/", response_model=schemas.Validation, status_code=status.HTTP_201_CREATED)
def create_validation(validation: schemas.ValidationCreate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Create new validation.
    ADMIN/DEVELOPER: Can create validations in any application
    END_USER: Can only create validations in their current session's application
    """
    # Validations are scoped by page, so resolve the application through it
    page = crud.get_page(db, page_id=validation.page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check application access
    application_access_required(page.application_id)(current_user, current_session, db)

    return crud.create_validation(db=db, validation=validation)


@router.put("/{validation_id}", response_model=schemas.Validation)
def update_validation(validation_id: int, validation: schemas.ValidationUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Update a validation.
    ADMIN/DEVELOPER: Can update any validation
    END_USER: Can only update validations in their current session's application
    """
    # Get the validation to check its application
    db_validation = crud.get_validation(db, validation_id=validation_id)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Get the application through validation -> page -> application
    application_id = db_validation.page.application_id if db_validation.page else None

    if application_id:
        # Check application access
        application_access_required(application_id)(current_user, current_session, db)

    db_validation = crud.update_validation(db=db, validation_id=validation_id, validation=validation)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return db_validation


@router.delete("/{validation_id}", response_model=schemas.Validation)
def delete_validation(validation_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user), current_session: models.Session = Depends(get_current_session)):
    """
    Delete a validation.
    ADMIN: Can delete any validation
    END_USER: Cannot delete validations (maintaining ADMIN-only restriction, but with app access check)
    """
    # Get the validation to check its application
    db_validation = crud.get_validation(db, validation_id=validation_id)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Get the application through validation -> page -> application
    application_id = db_validation.page.application_id if db_validation.page else None

    if application_id:
        # Check application access (for consistency, even though only ADMIN can delete)
        application_access_required(application_id)(current_user, current_session, db)

    # Additionally, enforce that only ADMIN can delete (maintaining existing restriction)
    if current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can delete validations"
        )

    db_validation = crud.delete_validation(db=db, validation_id=validation_id)
    if db_validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return db_validation