"""FastAPI security middleware integration."""

from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import auth_middleware, User
from .rate_limiter import default_limiter
from .validation import InputValidator


class SecurityMiddleware(BaseHTTPMiddleware):
    """Combined security middleware for FastAPI."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip security for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Rate limiting
        try:
            headers = await default_limiter.check(request)
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        for key, value in headers.items():
            response.headers[key] = str(value)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def setup_security(
    app: FastAPI,
    enable_cors: bool = True,
    cors_origins: list[str] = None,
    enable_rate_limiting: bool = True,
):
    """Setup security middleware for a FastAPI app."""
    
    # CORS
    if enable_cors:
        origins = cors_origins or [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Security middleware
    if enable_rate_limiting:
        app.add_middleware(SecurityMiddleware)
    
    # Add security endpoints
    @app.get("/security/status")
    async def security_status():
        return {
            "auth_enabled": auth_middleware.enabled,
            "rate_limiting": enable_rate_limiting,
            "cors_enabled": enable_cors,
        }
    
    return app
