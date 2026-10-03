from sqlalchemy.orm import Session

from .db import models
from . import schemas


# Application CRUD operations
def get_application(db: Session, application_id: int):
    return db.query(models.Application).filter(models.Application.id == application_id).first()


def get_applications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Application).offset(skip).limit(limit).all()


def create_application(db: Session, application: schemas.ApplicationCreate):
    db_app = models.Application(**application.dict())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def update_application(db: Session, application_id: int, application: schemas.ApplicationUpdate):
    db_app = db.query(models.Application).filter(models.Application.id == application_id).first()
    if db_app:
        update_data = application.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_app, key, value)
        db.commit()
        db.refresh(db_app)
    return db_app


def delete_application(db: Session, application_id: int):
    db_app = db.query(models.Application).filter(models.Application.id == application_id).first()
    if db_app:
        db.delete(db_app)
        db.commit()
    return db_app

# Page CRUD operations
def get_page(db: Session, page_id: int):
    return db.query(models.Page).filter(models.Page.id == page_id).first()


def get_pages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Page).offset(skip).limit(limit).all()


def get_pages_by_application(db: Session, application_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Page).filter(models.Page.application_id == application_id).offset(skip).limit(limit).all()


def create_page(db: Session, page: schemas.PageCreate):
    db_page = models.Page(**page.dict())
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page


def update_page(db: Session, page_id: int, page: schemas.PageUpdate):
    db_page = db.query(models.Page).filter(models.Page.id == page_id).first()
    if db_page:
        update_data = page.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_page, key, value)
        db.commit()
        db.refresh(db_page)
    return db_page


def delete_page(db: Session, page_id: int):
    db_page = db.query(models.Page).filter(models.Page.id == page_id).first()
    if db_page:
        db.delete(db_page)
        db.commit()
    return db_page


# Region CRUD operations
def get_region(db: Session, region_id: int):
    return db.query(models.Region).filter(models.Region.id == region_id).first()


def get_regions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Region).offset(skip).limit(limit).all()


def get_regions_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Region).filter(models.Region.page_id == page_id).offset(skip).limit(limit).all()


def get_regions_by_application(db: Session, application_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Region)
        .join(models.Page, models.Region.page_id == models.Page.id)
        .filter(models.Page.application_id == application_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_region(db: Session, region: schemas.RegionCreate):
    db_region = models.Region(**region.dict())
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


def update_region(db: Session, region_id: int, region: schemas.RegionUpdate):
    db_region = db.query(models.Region).filter(models.Region.id == region_id).first()
    if db_region:
        update_data = region.dict(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            setattr(db_region, key, value)
        db.commit()
        db.refresh(db_region)
    return db_region


def delete_region(db: Session, region_id: int):
    db_region = db.query(models.Region).filter(models.Region.id == region_id).first()
    if db_region:
        db.delete(db_region)
        db.commit()
    return db_region


# Item CRUD operations
def get_item(db: Session, item_id: int):
    return db.query(models.PageItem).filter(models.PageItem.id == item_id).first()


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PageItem).offset(skip).limit(limit).all()


def get_items_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.PageItem).filter(models.PageItem.page_id == page_id).offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.PageItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int, item: schemas.ItemUpdate):
    db_item = db.query(models.PageItem).filter(models.PageItem.id == item_id).first()
    if db_item:
        update_data = item.dict(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int):
    db_item = db.query(models.PageItem).filter(models.PageItem.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item


# Validation CRUD operations
def get_validation(db: Session, validation_id: int):
    return db.query(models.Validation).filter(models.Validation.id == validation_id).first()


def get_validations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Validation).offset(skip).limit(limit).all()


def get_validations_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Validation)
        .filter(models.Validation.page_id == page_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_validations_by_item(db: Session, page_id: int, item_name: str):
    return (
        db.query(models.Validation)
        .filter(
            models.Validation.page_id == page_id,
            models.Validation.item_name == item_name,
        )
        .all()
    )


def get_validations_by_application(db: Session, application_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Validation)
        .join(models.Page, models.Validation.page_id == models.Page.id)
        .filter(models.Page.application_id == application_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_validation(db: Session, validation: schemas.ValidationCreate):
    db_validation = models.Validation(**validation.dict())
    db.add(db_validation)
    db.commit()
    db.refresh(db_validation)
    return db_validation


def update_validation(db: Session, validation_id: int, validation: schemas.ValidationUpdate):
    db_validation = db.query(models.Validation).filter(models.Validation.id == validation_id).first()
    if db_validation:
        update_data = validation.dict(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            setattr(db_validation, key, value)
        db.commit()
        db.refresh(db_validation)
    return db_validation


def delete_validation(db: Session, validation_id: int):
    db_validation = db.query(models.Validation).filter(models.Validation.id == validation_id).first()
    if db_validation:
        db.delete(db_validation)
        db.commit()
    return db_validation


# LOV CRUD operations
def get_lov(db: Session, lov_id: int):
    return db.query(models.Lov).filter(models.Lov.id == lov_id).first()


def get_lov_by_name(db: Session, lov_name: str):
    return db.query(models.Lov).filter(models.Lov.lov_name == lov_name).first()


def get_lovs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Lov).offset(skip).limit(limit).all()


def get_lovs_by_application(db: Session, application_id: int, skip: int = 0, limit: int = 100):
    """LOVs are workspace-global: the table has no application or item foreign key.

    The application_id parameter is accepted so callers stay agnostic of that
    limitation; once apex_lovs is scoped per application this becomes a filter.
    """
    return get_lovs(db, skip=skip, limit=limit)


def create_lov(db: Session, lov: schemas.LovCreate):
    db_lov = models.Lov(**lov.dict())
    db.add(db_lov)
    db.commit()
    db.refresh(db_lov)
    return db_lov


def update_lov(db: Session, lov_id: int, lov: schemas.LovUpdate):
    db_lov = db.query(models.Lov).filter(models.Lov.id == lov_id).first()
    if db_lov:
        update_data = lov.dict(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            setattr(db_lov, key, value)
        db.commit()
        db.refresh(db_lov)
    return db_lov


def delete_lov(db: Session, lov_id: int):
    db_lov = db.query(models.Lov).filter(models.Lov.id == lov_id).first()
    if db_lov:
        db.delete(db_lov)
        db.commit()
    return db_lov


# Workspace user CRUD operations
def get_workspace_user(db: Session, user_id: int):
    return db.query(models.WorkspaceUser).filter(models.WorkspaceUser.id == user_id).first()


def get_workspace_user_by_username(db: Session, username: str):
    return db.query(models.WorkspaceUser).filter(models.WorkspaceUser.username == username).first()


def get_workspace_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WorkspaceUser).offset(skip).limit(limit).all()


def create_workspace_user(db: Session, user: schemas.WorkspaceUserCreate):
    db_user = models.WorkspaceUser(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_workspace_user(db: Session, user_id: int, user: schemas.WorkspaceUserUpdate):
    db_user = db.query(models.WorkspaceUser).filter(models.WorkspaceUser.id == user_id).first()
    if db_user:
        update_data = user.dict(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_workspace_user(db: Session, user_id: int):
    db_user = db.query(models.WorkspaceUser).filter(models.WorkspaceUser.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# Application session CRUD operations
def get_session(db: Session, session_id: str):
    return db.query(models.Session).filter(models.Session.session_id == session_id).first()


def get_sessions_by_user(db: Session, user_id: int, is_active: bool = None):
    query = db.query(models.Session).filter(models.Session.user_id == user_id)
    if is_active is not None:
        query = query.filter(models.Session.is_active == is_active)
    return query.all()


def get_session_by_user_and_app(
    db: Session,
    user_id: int = None,
    application_id: int = None,
    is_active: bool = None,
):
    """Most recent session for a user, optionally scoped to an application."""
    query = db.query(models.Session)
    if user_id is not None:
        query = query.filter(models.Session.user_id == user_id)
    if application_id is not None:
        query = query.filter(models.Session.application_id == application_id)
    if is_active is not None:
        query = query.filter(models.Session.is_active == is_active)
    return query.order_by(models.Session.created_at.desc()).first()