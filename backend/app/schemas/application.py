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

class ApplicationUpdate(ApplicationBase):
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Application(ApplicationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True