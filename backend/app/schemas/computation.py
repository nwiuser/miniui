from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ComputationBase(BaseModel):
    page_id: int
    computation_point: str
    computation_type: str
    computation_item: str
    computation_value: Optional[str] = None
    computation_condition_type: Optional[str] = None
    computation_condition_expression: Optional[str] = None
    sequence: Optional[int] = 1
    is_active: Optional[bool] = True

class ComputationCreate(ComputationBase):
    pass

class ComputationUpdate(ComputationBase):
    page_id: Optional[int] = None
    computation_point: Optional[str] = None
    computation_type: Optional[str] = None
    computation_item: Optional[str] = None
    computation_value: Optional[str] = None
    computation_condition_type: Optional[str] = None
    computation_condition_expression: Optional[str] = None
    sequence: Optional[int] = None
    is_active: Optional[bool] = None

class Computation(ComputationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True