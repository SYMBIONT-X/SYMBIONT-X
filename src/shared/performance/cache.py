"""Caching system for SYMBIONT-X."""

import os
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Callable, TypeVar, Dict
from functools import wraps
from dataclasses import dataclass
import threading


T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cached value with metadata."""
    value: Any
    expires_at: datetime
    created_at: datetime = None
    hits: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class Cache:
    """In-memory cache with TTL support and Redis-ready interface."""
    
    def __init__(
        self,
        default_ttl: int = 300,  # 5 minutes
        max_size: int = 1000,
        redis_url: Optional[str] = None,
    ):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._store: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._redis = None
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}
        
        # Try to connect to Redis if URL provided
        redis_url = redis_url or os.getenv("REDIS_URL")
        if redis_url:
            self._init_redis(redis_url)
    
    def _init_redis(self, redis_url: str):
        """Initialize Redis connection."""
        try:
            import redis
            self._redis = redis.from_url(redis_url)
            self._redis.ping()
        except Exception as e:
            print(f"Redis connection failed, using in-memory cache: {e}")
            self._redis = None
    
    def _generate_key(self, key: str, namespace: str = "default") -> str:
        """Generate a namespaced cache key."""
        return f"symbiontx:{namespace}:{key}"
    
    def _evict_expired(self):
        """Remove expired entries."""
        with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired]
            for k in expired:
                del self._store[k]
    
    def _evict_lru(self):
        """Evict least recently used entries if over max size."""
        with self._lock:
            if len(self._store) >= self.max_size:
                # Sort by hits (LFU) and created_at (LRU)
                sorted_keys = sorted(
                    self._store.keys(),
                    key=lambda k: (self._store[k].hits, self._store[k].created_at)
                )
                # Remove oldest 10%
                to_remove = sorted_keys[:max(1, len(sorted_keys) // 10)]
                for k in to_remove:
                    del self._store[k]
    
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get a value from cache."""
        full_key = self._generate_key(key, namespace)
        
        # Try Redis first
        if self._redis:
            try:
                value = self._redis.get(full_key)
                if value:
                    self._stats["hits"] += 1
                    return json.loads(value)
            except Exception:
                pass
        
        # Fall back to in-memory
        with self._lock:
            entry = self._store.get(full_key)
            if entry:
                if entry.is_expired:
                    del self._store[full_key]
                    self._stats["misses"] += 1
                    return None
                entry.hits += 1
                self._stats["hits"] += 1
                return entry.value
        
        self._stats["misses"] += 1
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default",
    ):
        """Set a value in cache."""
        full_key = self._generate_key(key, namespace)
        ttl = ttl or self.default_ttl
        
        # Try Redis first
        if self._redis:
            try:
                self._redis.setex(full_key, ttl, json.dumps(value, default=str))
                self._stats["sets"] += 1
                return
            except Exception:
                pass
        
        # Fall back to in-memory
        self._evict_expired()
        self._evict_lru()
        
        with self._lock:
            self._store[full_key] = CacheEntry(
                value=value,
                expires_at=datetime.utcnow() + timedelta(seconds=ttl),
            )
            self._stats["sets"] += 1
    
    def delete(self, key: str, namespace: str = "default"):
        """Delete a value from cache."""
        full_key = self._generate_key(key, namespace)
        
        if self._redis:
            try:
                self._redis.delete(full_key)
            except Exception:
                pass
        
        with self._lock:
            if full_key in self._store:
                del self._store[full_key]
                self._stats["deletes"] += 1
    
    def clear(self, namespace: Optional[str] = None):
        """Clear cache entries."""
        if namespace:
            pattern = f"symbiontx:{namespace}:*"
            with self._lock:
                keys_to_delete = [k for k in self._store.keys() if k.startswith(f"symbiontx:{namespace}:")]
                for k in keys_to_delete:
                    del self._store[k]
        else:
            with self._lock:
                self._store.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0
        total = self._stats["hits"] + self._stats["misses"]
        if total > 0:
            hit_rate = self._stats["hits"] / total * 100
        
        return {
            **self._stats,
            "size": len(self._store),
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 2),
            "redis_connected": self._redis is not None,
        }


# Global cache instance
cache = Cache()


def cached(
    ttl: int = 300,
    namespace: str = "default",
    key_builder: Optional[Callable] = None,
):
    """Decorator to cache function results."""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key, namespace)
            if result is not None:
                return result
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl, namespace)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key, namespace)
            if result is not None:
                return result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl, namespace)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
