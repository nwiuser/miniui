from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicationBase(BaseModel):
    name: str
    alias: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    # All fields optional: PUT takes the id from the path and crud applies
    # only the supplied fields (exclude_unset=True).
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Application(ApplicationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True