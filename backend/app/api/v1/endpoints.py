from fastapi import APIRouter

from . import applications

# Create the main API router for v1
api_router = APIRouter()

# Include all routers from endpoint modules
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])