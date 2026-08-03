from pydantic import BaseModel
from typing import Optional, Dict, Any


class Token(BaseModel):
    access_token: str
    token_type: str
    # Optional user info returned upon login
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    administrator_role: Optional[str] = None

    class Config:
        orm_mode = True