from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    page_id: int
    region_id: Optional[int] = None
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

class ItemUpdate(BaseModel):
    # All fields optional: PUT takes the id from the path and crud applies
    # only the supplied fields (exclude_unset=True, excluding "id").
    page_id: Optional[int] = None
    region_id: Optional[int] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    item_type: Optional[str] = None
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
        from_attributes = True