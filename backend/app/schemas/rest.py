from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class RestDataSourceBase(BaseModel):
    application_id: int
    name: str
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 30
    is_active: Optional[bool] = True


class RestDataSourceCreate(RestDataSourceBase):
    pass


class RestDataSourceUpdate(BaseModel):
    application_id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None


class RestDataSource(RestDataSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RestDataSourceExecuteResponse(BaseModel):
    data_source_id: int
    name: str
    method: str
    url: str
    status_code: int
    data: Any
    mapped_items: Optional[Dict[str, str]] = None


class ApplicationMetadata(BaseModel):
    application: Dict[str, Any]
    pages: List[Dict[str, Any]]


__all__ = [
    "RestDataSource", "RestDataSourceCreate", "RestDataSourceUpdate",
    "RestDataSourceExecuteResponse", "ApplicationMetadata",
]