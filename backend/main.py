from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

from app.api import api_router

app = FastAPI(
    title="Open Source APEX Equivalent",
    description="API for building APEX-like applications",
    version="0.1.0",
)

# Security middleware to add security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # HSTS would be added only over HTTPS; we can conditionally add if request is secure
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content Security Policy (basic)
        # Adjust as needed for your application
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CSRF protection middleware
class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_paths=None):
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or [])

    async def dispatch(self, request: Request, call_next):
        # If request method is safe, skip CSRF check
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return await call_next(request)
        # If path is exempt, skip CSRF check
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        # Require custom header X-Requested-With: XMLHttpRequest
        header_value = request.headers.get("X-Requested-With")
        if header_value != "XMLHttpRequest":
            # For requests that expect JSON, we can return JSON error
            return Response(
                content='{"detail":"CSRF validation failed: Missing X-Requested-With header"}',
                status_code=403,
                media_type="application/json"
            )
        return await call_next(request)

# Define exempt paths (adjust as needed)
exempt_paths = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/auth/login",
    "/auth/logout",
    "/",  # root endpoint
]

# Add CSRF protection middleware
app.add_middleware(CSRFProtectionMiddleware, exempt_paths=exempt_paths)

# Trusted host middleware (adjust allowed hosts as needed)
# For development, we allow all; in production, specify your domain(s)
allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
if "*" not in allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Set up CORS
# In production, restrict allow_origins to your frontend domain(s)
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Include API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Open Source APEX Equivalent API", "docs": "/docs"}