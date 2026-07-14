from fastapi import APIRouter

from app.api.v1.endpoints import api_router as v1_router

api_router = APIRouter()

# Include versioned routers
api_router.include_router(v1_router, prefix="/v1")

@api_router.get("/")
async def root():
    return {"message": "API", "version": "0.1.0"}