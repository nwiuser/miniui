from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    page_id: int
    name: str
    alias: Optional[str] = None
    item_type: str
    label: Optional[str] = None
    placeholder: Optional[str] = None
    default_value: Optional[str] = None
    is_required: Optional[bool] = False
    is_active: Optional[bool] = True

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    id: int
    name: Optional[str] = None
    alias: Optional[str] = None
    label: Optional[str] = None
    placeholder: Optional[str] = None
    default_value: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None

class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True