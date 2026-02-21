"""Authentication middleware for SYMBIONT-X."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt


# Configuration
AZURE_AD_TENANT_ID = os.getenv("AZURE_AD_TENANT_ID", "")
AZURE_AD_CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "symbiont-x-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security scheme
security = HTTPBearer(auto_error=False)


class User:
    """Authenticated user model."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        name: str,
        roles: list[str],
        tenant_id: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.roles = roles
        self.tenant_id = tenant_id
    
    def has_role(self, role: str) -> bool:
        return role in self.roles
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "roles": self.roles,
            "tenant_id": self.tenant_id,
        }


class AuthMiddleware:
    """Authentication middleware supporting Azure AD and JWT."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._azure_ad_configured = bool(AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID)
    
    async def authenticate(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None,
    ) -> Optional[User]:
        """Authenticate request and return user."""
        
        if not self.enabled:
            # Return default dev user when auth is disabled
            return User(
                user_id="dev-user",
                email="dev@symbiont-x.local",
                name="Development User",
                roles=["admin", "developer", "security_team"],
            )
        
        if not credentials:
            return None
        
        token = credentials.credentials
        
        try:
            # Try JWT token first
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            return User(
                user_id=payload.get("sub", "unknown"),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                roles=payload.get("roles", []),
                tenant_id=payload.get("tenant_id"),
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            # If Azure AD is configured, try to validate as Azure AD token
            if self._azure_ad_configured:
                return await self._validate_azure_ad_token(token)
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def _validate_azure_ad_token(self, token: str) -> User:
        """Validate Azure AD token."""
        
        # In production, would validate against Azure AD
        # For now, decode without verification for demo
        try:
            # Decode without verification (demo only)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return User(
                user_id=payload.get("oid", payload.get("sub", "unknown")),
                email=payload.get("preferred_username", payload.get("email", "")),
                name=payload.get("name", ""),
                roles=payload.get("roles", ["developer"]),
                tenant_id=payload.get("tid"),
            )
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid Azure AD token")
    
    @staticmethod
    def create_token(user: User, expires_hours: int = JWT_EXPIRATION_HOURS) -> str:
        """Create a JWT token for a user."""
        
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "name": user.name,
            "roles": user.roles,
            "tenant_id": user.tenant_id,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow(),
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Global middleware instance
auth_middleware = AuthMiddleware(enabled=os.getenv("AUTH_ENABLED", "false").lower() == "true")


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """Dependency to get current authenticated user."""
    
    user = await auth_middleware.authenticate(request, credentials)
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return user


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Dependency to get current user (optional)."""
    
    return await auth_middleware.authenticate(request, credentials)


def require_auth(func):
    """Decorator to require authentication."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        if request:
            user = await get_current_user(request)
            kwargs["current_user"] = user
        
        return await func(*args, **kwargs)
    
    return wrapper
