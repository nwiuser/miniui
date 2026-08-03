from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Any

class RegionBase(BaseModel):
    page_id: int
    name: str
    region_type: str
    template_options: Optional[Any] = None
    position: Optional[int] = 0
    is_active: Optional[bool] = True

class RegionCreate(RegionBase):
    pass

class RegionUpdate(RegionBase):
    id: int
    name: Optional[str] = None
    alias: Optional[str] = None
    region_type: Optional[str] = None
    template_options: Optional[Any] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None

class Region(RegionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True