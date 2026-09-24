from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PageProcessBase(BaseModel):
    page_id: int
    name: str
    process_type: str
    process_code: Optional[str] = None
    execution_sequence: Optional[int] = 10
    execution_point: Optional[str] = "ON_SUBMIT_BEFORE_COMPUTATION"
    is_active: Optional[bool] = True


class PageProcessCreate(PageProcessBase):
    pass


class PageProcessUpdate(BaseModel):
    page_id: Optional[int] = None
    name: Optional[str] = None
    process_type: Optional[str] = None
    process_code: Optional[str] = None
    execution_sequence: Optional[int] = None
    execution_point: Optional[str] = None
    is_active: Optional[bool] = None


class PageProcess(PageProcessBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
