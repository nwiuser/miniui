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
    is_public: Optional[bool] = False


class PageCreate(PageBase):
    pass


class PageUpdate(BaseModel):
    # All fields optional: PUT takes the id from the path and crud applies
    # only the supplied fields (exclude_unset=True).
    application_id: Optional[int] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    page_number: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class Page(PageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True