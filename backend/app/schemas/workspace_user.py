from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkspaceUserBase(BaseModel):
    username: str
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    administrator_role: Optional[str] = None
    account_expiry_date: Optional[datetime] = None
    account_locked: Optional[bool] = False
    failed_access_attempts: Optional[int] = 0
    change_password_on_first_use: Optional[bool] = False
    first_name_phonetic: Optional[str] = None
    last_name_phonetic: Optional[str] = None

class WorkspaceUserCreate(WorkspaceUserBase):
    pass

class WorkspaceUserUpdate(WorkspaceUserBase):
    username: Optional[str] = None
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    administrator_role: Optional[str] = None
    account_expiry_date: Optional[datetime] = None
    account_locked: Optional[bool] = None
    failed_access_attempts: Optional[int] = None
    change_password_on_first_use: Optional[bool] = None
    first_name_phonetic: Optional[str] = None
    last_name_phonetic: Optional[str] = None

class WorkspaceUser(WorkspaceUserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True