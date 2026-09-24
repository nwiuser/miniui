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