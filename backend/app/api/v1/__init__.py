from .endpoints import applications

# Include routers in the API v1 router
def include_routers(api_router):
    api_router.include_router(applications.router)