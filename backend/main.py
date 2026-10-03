from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

from app.api import api_router
from app.core.cache import application_metadata_cache
from app.core.security.rate_limit import RateLimitMiddleware

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

    def _is_exempt(self, path: str) -> bool:
        """True when the path is exempt, either exactly or below an exempt prefix.

        Matching is done on path segments, not raw prefixes: a plain
        ``startswith`` test makes ``"/"`` exempt every route, which silently
        disables the middleware, and would also exempt ``/api/v1/auth/login-extra``
        for an entry of ``/api/v1/auth/login``.
        """
        for exempt in self.exempt_paths:
            prefix = exempt.rstrip("/")
            if path == exempt or path == prefix:
                return True
            # An entry of "/" means the root endpoint only; treating it as a
            # prefix would exempt every path.
            if prefix and path.startswith(prefix + "/"):
                return True
        return False

    async def dispatch(self, request: Request, call_next):
        # If request method is safe, skip CSRF check
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return await call_next(request)
        # If path is exempt, skip CSRF check
        if self._is_exempt(request.url.path):
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
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    # Runtime page submissions arrive as plain browser form posts, which cannot
    # carry the X-Requested-With header. They are protected by the session and
    # page-visibility checks instead.
    "/api/v1/pages",
]

# Add CSRF protection middleware
app.add_middleware(CSRFProtectionMiddleware, exempt_paths=exempt_paths)

# Add rate limiting for auth endpoints
app.add_middleware(RateLimitMiddleware, paths=["/api/v1/auth/login"])

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
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health():
    """Liveness probe used by Docker Compose and Kubernetes."""
    return {
        "status": "ok",
        "service": "apexos-backend",
        "version": app.version,
        "metadata_cache": application_metadata_cache.stats(),
    }


@app.get("/")
async def root():
    return {"message": "Welcome to Open Source APEX Equivalent API", "docs": "/docs"}