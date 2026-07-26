from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LovBase(BaseModel):
    lov_name: str
    lov_definition: Optional[str] = None
    is_static: Optional[bool] = False
    display_extra: Optional[bool] = True
    translation_applicable: Optional[bool] = False
    is_translatable: Optional[bool] = False
    static_values: Optional[str] = None
    is_enterable: Optional[bool] = False
    show_null_value: Optional[bool] = False
    null_text: Optional[str] = None
    null_value: Optional[str] = None
    apex_item_height: Optional[int] = None
    apex_item_width: Optional[int] = None
    is_active: Optional[bool] = True

class LovCreate(LovBase):
    pass

class LovUpdate(LovBase):
    lov_name: Optional[str] = None
    lov_definition: Optional[str] = None
    is_static: Optional[bool] = None
    display_extra: Optional[bool] = None
    translation_applicable: Optional[bool] = None
    is_translatable: Optional[bool] = None
    static_values: Optional[str] = None
    is_enterable: Optional[bool] = None
    show_null_value: Optional[bool] = None
    null_text: Optional[str] = None
    null_value: Optional[str] = None
    apex_item_height: Optional[int] = None
    apex_item_width: Optional[int] = None
    is_active: Optional[bool] = None

class Lov(LovBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True