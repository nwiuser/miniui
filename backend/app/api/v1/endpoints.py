from fastapi import APIRouter

from . import applications, lov, validation, workspace_user, pages

# Create the main API router for v1
api_router = APIRouter()

# Include all routers from endpoint modules
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(lov.router, prefix="/lovs", tags=["lovs"])
api_router.include_router(validation.router, prefix="/validations", tags=["validations"])
api_router.include_router(workspace_user.router, prefix="/workspace-users", tags=["workspace-users"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])