from fastapi import APIRouter

from . import applications, lov, validation, workspace_user, pages, auth, region, item, render, process, computation

# Create the main API router for v1
api_router = APIRouter()

# Include all routers from endpoint modules
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(lov.router, tags=["lovs"])
api_router.include_router(validation.router, tags=["validations"])
api_router.include_router(workspace_user.router, tags=["workspace-users"])
api_router.include_router(pages.router, tags=["pages"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(region.router, tags=["regions"])
api_router.include_router(item.router, tags=["items"])
api_router.include_router(render.router, tags=["render"])
api_router.include_router(process.router, prefix="/processes", tags=["processes"])
api_router.include_router(computation.router, prefix="/computations", tags=["computations"])