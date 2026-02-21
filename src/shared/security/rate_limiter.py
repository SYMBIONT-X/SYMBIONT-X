"""Rate limiting for SYMBIONT-X APIs."""

import time
from collections import defaultdict
from typing import Optional, Dict, Tuple
from functools import wraps

from fastapi import HTTPException, Request


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
    ):
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.burst = burst_size
        
        # Storage: key -> (tokens, last_update, hour_count, hour_start)
        self._buckets: Dict[str, Tuple[float, float, int, float]] = defaultdict(
            lambda: (burst_size, time.time(), 0, time.time())
        )
    
    def _get_key(self, request: Request, key_type: str = "ip") -> str:
        """Generate rate limit key."""
        
        if key_type == "ip":
            # Get client IP
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        
        elif key_type == "user":
            # Get user ID from request state
            user = getattr(request.state, "user", None)
            if user:
                return f"user:{user.user_id}"
            return self._get_key(request, "ip")
        
        return "global"
    
    def is_allowed(self, request: Request, key_type: str = "ip") -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed under rate limits."""
        
        key = self._get_key(request, key_type)
        now = time.time()
        
        tokens, last_update, hour_count, hour_start = self._buckets[key]
        
        # Refill tokens based on time elapsed
        elapsed = now - last_update
        tokens = min(self.burst, tokens + elapsed * (self.rpm / 60.0))
        
        # Reset hourly counter if needed
        if now - hour_start >= 3600:
            hour_count = 0
            hour_start = now
        
        # Check limits
        headers = {
            "X-RateLimit-Limit": self.rpm,
            "X-RateLimit-Remaining": max(0, int(tokens) - 1),
            "X-RateLimit-Reset": int(last_update + 60),
        }
        
        if tokens < 1:
            return False, headers
        
        if hour_count >= self.rph:
            return False, headers
        
        # Consume token
        self._buckets[key] = (tokens - 1, now, hour_count + 1, hour_start)
        
        return True, headers
    
    async def check(self, request: Request, key_type: str = "ip"):
        """Check rate limit and raise exception if exceeded."""
        
        allowed, headers = self.is_allowed(request, key_type)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={k: str(v) for k, v in headers.items()},
            )
        
        return headers


# Default rate limiter instances
default_limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)
strict_limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
scan_limiter = RateLimiter(requests_per_minute=5, requests_per_hour=50, burst_size=3)


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    key_type: str = "ip",
):
    """Decorator for rate limiting endpoints."""
    
    limiter = RateLimiter(requests_per_minute, requests_per_hour)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                await limiter.check(request, key_type)
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
