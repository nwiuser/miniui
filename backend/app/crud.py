from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

# Application CRUD operations
def get_application(db: Session, application_id: int):
    return db.query(models.Application).filter(models.Application.id == application_id).first()

def get_applications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Application).offset(skip).limit(limit).all()

def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = models.Application(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def update_application(db: Session, application_id: int, application: schemas.ApplicationUpdate):
    db_application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if db_application:
        update_data = application.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_application, key, value)
        db.commit()
        db.refresh(db_application)
    return db_application

def delete_application(db: Session, application_id: int):
    db_application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if db_application:
        db.delete(db_application)
        db.commit()
    return db_application

# Validation CRUD operations
def get_validation(db: Session, validation_id: int):
    return db.query(models.Validation).filter(models.Validation.id == validation_id).first()

def get_validations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Validation).offset(skip).limit(limit).all()

def get_validations_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Validation).filter(models.Validation.page_id == page_id).offset(skip).limit(limit).all()

def get_validations_by_item(db: Session, page_id: int, item_name: str):
    return db.query(models.Validation).filter(
        models.Validation.page_id == page_id,
        models.Validation.item_name == item_name
    ).all()

def create_validation(db: Session, validation: schemas.ValidationCreate):
    db_validation = models.Validation(**validation.dict())
    db.add(db_validation)
    db.commit()
    db.refresh(db_validation)
    return db_validation

def update_validation(db: Session, validation_id: int, validation: schemas.ValidationUpdate):
    db_validation = db.query(models.Validation).filter(models.Validation.id == validation_id).first()
    if db_validation:
        update_data = validation.dict(exclude_unset=True)
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

def create_lov(db: Session, lov: schemas.LovCreate):
    db_lov = models.Lov(**lov.dict())
    db.add(db_lov)
    db.commit()
    db.refresh(db_lov)
    return db_lov

def update_lov(db: Session, lov_id: int, lov: schemas.LovUpdate):
    db_lov = db.query(models.Lov).filter(models.Lov.id == lov_id).first()
    if db_lov:
        update_data = lov.dict(exclude_unset=True)
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

# WorkspaceUser CRUD operations
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
        update_data = user.dict(exclude_unset=True)
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