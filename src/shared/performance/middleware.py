"""Performance middleware for SYMBIONT-X."""

import time
import gzip
from typing import Callable
from io import BytesIO

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track and optimize performance."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_threshold = slow_request_threshold
        self._request_times = []
        self._max_samples = 1000
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.perf_counter() - start_time
        duration_ms = round(duration * 1000, 2)
        
        # Track timing
        self._request_times.append(duration)
        if len(self._request_times) > self._max_samples:
            self._request_times = self._request_times[-self._max_samples:]
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        
        # Log slow requests
        if duration > self.slow_threshold:
            print(f"SLOW REQUEST: {request.method} {request.url.path} took {duration_ms}ms")
        
        return response
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        if not self._request_times:
            return {"avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0}
        
        sorted_times = sorted(self._request_times)
        n = len(sorted_times)
        
        return {
            "total_requests": n,
            "avg_ms": round(sum(sorted_times) / n * 1000, 2),
            "p50_ms": round(sorted_times[n // 2] * 1000, 2),
            "p95_ms": round(sorted_times[int(n * 0.95)] * 1000, 2),
            "p99_ms": round(sorted_times[int(n * 0.99)] * 1000, 2),
            "min_ms": round(min(sorted_times) * 1000, 2),
            "max_ms": round(max(sorted_times) * 1000, 2),
        }


# Global middleware instance for stats access
_perf_middleware = None


def setup_performance(
    app: FastAPI,
    enable_gzip: bool = True,
    enable_timing: bool = True,
    slow_threshold: float = 1.0,
):
    """Setup performance optimizations for FastAPI app."""
    
    global _perf_middleware
    
    # GZip compression
    if enable_gzip:
        app.add_middleware(GZipMiddleware, minimum_size=500)
    
    # Performance tracking
    if enable_timing:
        _perf_middleware = PerformanceMiddleware(app, slow_threshold)
        app.add_middleware(PerformanceMiddleware, slow_request_threshold=slow_threshold)
    
    # Cache headers for static content
    @app.middleware("http")
    async def add_cache_headers(request: Request, call_next):
        response = await call_next(request)
        
        # Add cache headers for specific paths
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=86400"
        elif request.url.path in ["/health", "/agents"]:
            response.headers["Cache-Control"] = "public, max-age=5"
        
        return response
    
    # Performance stats endpoint
    @app.get("/performance/stats")
    async def performance_stats():
        from .cache import cache
        
        return {
            "cache": cache.get_stats(),
            "requests": _perf_middleware.get_stats() if _perf_middleware else {},
        }
    
    return app
