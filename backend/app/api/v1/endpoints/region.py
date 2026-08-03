"""
Region Endpoints
Handles HTTP requests for region management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..db.session import get_db
from .. import crud
from ..core.auth import require_role, application_access_required, get_current_user


router = APIRouter(
    prefix="/regions",
    tags=["regions"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Region])
def read_regions(skip: int = 0, limit: int = 100, page_id: Optional[int] = None, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Retrieve regions. Optionally filter by page_id.
    ADMIN/DEVELOPER: Can access all regions
    END_USER: Can only access regions in their current session's application
    """
    # If filtering by page_id, check application access first
    if page_id:
        # Get the application ID from the page
        page = crud.get_page(db, page_id=page_id)
        if page:
            application_id = page.application_id
            # Check application access
            application_access_required(application_id)(current_user, None, db)

    # For ADMIN/DEVELOPER, show all; for END_USER, filter by session application
    if current_user.administrator_role in ["ADMIN", "DEVELOPER"]:
        regions = crud.get_regions(db, skip=skip, limit=limit)
    else:
        # END_USER: get regions only from their current session's application
        if current_user.session_id:
            session = crud.get_session(db, session_id=current_user.session_id)
            if session and session.application_id:
                regions = crud.get_regions_by_application(db, application_id=session.application_id, skip=skip, limit=limit)
            else:
                regions = []  # No active session, no access
        else:
            regions = []  # No session, no access

    return regions


@router.get("/{region_id}", response_model=schemas.Region)
def read_region(region_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Retrieve a specific region by ID.
    ADMIN/DEVELOPER: Can access any region
    END_USER: Can only access regions in their current session's application
    """
    db_region = crud.get_region(db, region_id=region_id)
    if db_region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    # Check application access through the region's page
    if db_region.page:
        application_id = db_region.page.application_id
        application_access_required(application_id)(current_user, None, db)
    # If region has no page, allow access (edge case - could be global region)

    return db_region


@router.post("/", response_model=schemas.Region, status_code=status.HTTP_201_CREATED)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Create a new region.
    ADMIN/DEVELOPER: Can create regions in any application
    END_USER: Can only create regions in their current session's application
    """
    # Check if the region specifies a page_id
    if region.page_id:
        # Get the page to verify it exists and get its application_id
        from .. import crud
        page = crud.get_page(db, page_id=region.page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")

        # Check application access
        application_id = page.application_id
        application_access_required(application_id)(current_user, None, db)
    # If no page_id specified, ADMIN/DEVELOPER/ADMIN can still create (global region)
    # END_USER without page_id would need special handling - for now require page_id

    return crud.create_region(db=db, region=region)


@router.put("/{region_id}", response_model=schemas.Region)
def update_region(region_id: int, region: schemas.RegionUpdate, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Update an existing region.
    ADMIN/DEVELOPER: Can update any region
    END_USER: Can only update regions in their current session's application
    """
    db_region = crud.get_region(db, region_id=region_id)
    if db_region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    # Check application access through the region's page
    if db_region.page:
        application_id = db_region.page.application_id
        application_access_required(application_id)(current_user, None, db)
    # If region has no page, allow ADMIN/DEVELOPER access (global region)

    db_region = crud.update_region(db, region_id=region_id, region=region)
    if db_region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return db_region


@router.delete("/{region_id}", response_model=schemas.Region)
def delete_region(region_id: int, db: Session = Depends(get_db), current_user: models.WorkspaceUser = Depends(get_current_user)):
    """
    Delete a region.
    ADMIN: Can delete any region
    DEVELOPER: Can delete any region (typically same as ADMIN for regions)
    END_USER: Cannot delete regions (maintaining ADMIN-only restriction for delete, but with app access check)
    """
    db_region = crud.get_region(db, region_id=region_id)
    if db_region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    # Check application access through the region's page (for END_USER restriction insight)
    # Even though only ADMIN can delete, we still validate app access for consistency
    if db_region.page:
        application_id = db_region.page.application_id
        application_access_required(application_id)(current_user, None, db)
    # For regions without pages, allow ADMIN access

    # Additionally, enforce that only ADMIN can delete (keeping existing stricter rule)
    if current_user.administrator_role not in ["ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can delete regions"
        )

    db_region = crud.delete_region(db, region_id=region_id)
    if db_region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return db_region