from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from .... import schemas
from ....db import models
from ....db.session import get_db
from ....core.auth import (
    get_current_user,
    get_current_session,
    application_access_required,
)
from ....core.rest import RestDataSourceService, RestClientError
from ....core.session.service import SessionService


router = APIRouter(
    prefix="/rest-data-sources",
    tags=["rest-data-sources"],
    responses={404: {"description": "Not found"}},
)


def _check_access(db: Session, source, current_user, current_session) -> None:
    application_access_required(source.application_id)(current_user, current_session, db)


@router.get("", response_model=List[schemas.RestDataSource])
def get_rest_data_sources(
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session),
):
    """
    Retrieve REST data sources.
    ADMIN/DEVELOPER: All sources. END_USER: Only sources in their session's application.
    """
    query = db.query(models.RestDataSource)

    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        if application_id and application_id != current_session.application_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this application",
            )
        query = query.filter(
            models.RestDataSource.application_id == current_session.application_id
        )
    elif application_id:
        query = query.filter(models.RestDataSource.application_id == application_id)

    return query.order_by(models.RestDataSource.name).all()


@router.get("/{source_id}", response_model=schemas.RestDataSource)
def get_rest_data_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session),
):
    source = db.query(models.RestDataSource).filter(models.RestDataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="REST data source not found")
    _check_access(db, source, current_user, current_session)
    return source


@router.post("", response_model=schemas.RestDataSource, status_code=status.HTTP_201_CREATED)
def create_rest_data_source(
    source: schemas.RestDataSourceCreate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session),
):
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    application = db.query(models.Application).filter(
        models.Application.id == source.application_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application_access_required(application.id)(current_user, current_session, db)

    db_source = models.RestDataSource(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.put("/{source_id}", response_model=schemas.RestDataSource)
def update_rest_data_source(
    source_id: int,
    source: schemas.RestDataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session),
):
    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    db_source = db.query(models.RestDataSource).filter(models.RestDataSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="REST data source not found")
    _check_access(db, db_source, current_user, current_session)

    update_data = source.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_source, key, value)

    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rest_data_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session),
):
    if current_user.administrator_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can delete REST data sources",
        )
    db_source = db.query(models.RestDataSource).filter(models.RestDataSource.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="REST data source not found")
    _check_access(db, db_source, current_user, current_session)

    db.delete(db_source)
    db.commit()


@router.post("/{source_id}/execute", response_model=schemas.RestDataSourceExecuteResponse)
def execute_rest_data_source(
    source_id: int,
    body: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: models.WorkspaceUser = Depends(get_current_user),
    current_session: models.Session = Depends(get_current_session),
):
    """
    Execute a REST data source server-side and return the parsed response.

    END_USER may only execute read-only (GET) sources within their session's
    application. State-changing sources require ADMIN/DEVELOPER.
    """
    source = db.query(models.RestDataSource).filter(models.RestDataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="REST data source not found")
    _check_access(db, source, current_user, current_session)

    if current_user.administrator_role not in ["ADMIN", "DEVELOPER"]:
        if (source.method or "GET").upper() != "GET":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="END_USER can only execute read-only REST data sources",
            )

    body = body or {}
    payload = body.get("payload")
    page_id = body.get("page_id")

    service = RestDataSourceService(db)
    try:
        result = service.execute(source, payload=payload)
    except RestClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    mapped = {}
    if page_id and current_session and source.response_mapping:
        session_service = SessionService(db)
        mapped = service.apply_response_mapping(
            source,
            result["data"],
            current_session.session_id,
            int(page_id),
            session_service,
        )

    return schemas.RestDataSourceExecuteResponse(
        data_source_id=source.id,
        name=source.name,
        method=(source.method or "GET").upper(),
        url=source.url,
        status_code=result["status_code"],
        data=result["data"],
        mapped_items=mapped or None,
    )