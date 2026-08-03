from pydantic schemas/page.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PageBase(BaseModel):
    application_id: int
    name: str
    alias: Optional[str] = None
    page_number: int
    description: Optional[str] = None
    is_active: Optional[bool] = True


class PageCreate(PageBase):
    pass


class PageUpdate(PageBase):
    id: int
    name: Optional[str] = None
    alias: Optional[str] = None
    page_number: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Page(PageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True