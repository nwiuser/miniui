from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ValidationBase(BaseModel):
    page_id: int
    item_name: str
    validation_type: str
    validation_expression: Optional[str] = None
    error_message: Optional[str] = None
    when_button_pressed: Optional[str] = None
    condition_type: Optional[str] = None
    condition_expression: Optional[str] = None
    is_active: Optional[bool] = True
    sequence: Optional[int] = 1

class ValidationCreate(ValidationBase):
    pass

class ValidationUpdate(ValidationBase):
    page_id: Optional[int] = None
    item_name: Optional[str] = None
    validation_type: Optional[str] = None
    validation_expression: Optional[str] = None
    error_message: Optional[str] = None
    when_button_pressed: Optional[str] = None
    condition_type: Optional[str] = None
    condition_expression: Optional[str] = None
    is_active: Optional[bool] = None
    sequence: Optional[int] = None

class Validation(ValidationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True