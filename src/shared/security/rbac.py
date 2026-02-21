"""Role-Based Access Control for SYMBIONT-X."""

from enum import Enum
from typing import List, Optional, Set
from functools import wraps

from fastapi import HTTPException, Request

from .auth import User, get_current_user


class Role(str, Enum):
    """Available roles in SYMBIONT-X."""
    ADMIN = "admin"
    SECURITY_TEAM = "security_team"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Available permissions."""
    # Scan permissions
    SCAN_CREATE = "scan:create"
    SCAN_READ = "scan:read"
    SCAN_DELETE = "scan:delete"
    
    # Vulnerability permissions
    VULN_READ = "vulnerability:read"
    VULN_UPDATE = "vulnerability:update"
    VULN_DISMISS = "vulnerability:dismiss"
    
    # Remediation permissions
    REMEDIATION_CREATE = "remediation:create"
    REMEDIATION_APPROVE = "remediation:approve"
    REMEDIATION_EXECUTE = "remediation:execute"
    
    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_CANCEL = "workflow:cancel"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_AUDIT = "admin:audit"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    
    Role.SECURITY_TEAM: {
        Permission.SCAN_CREATE,
        Permission.SCAN_READ,
        Permission.VULN_READ,
        Permission.VULN_UPDATE,
        Permission.VULN_DISMISS,
        Permission.REMEDIATION_CREATE,
        Permission.REMEDIATION_APPROVE,
        Permission.REMEDIATION_EXECUTE,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_CANCEL,
        Permission.ADMIN_AUDIT,
    },
    
    Role.DEVELOPER: {
        Permission.SCAN_CREATE,
        Permission.SCAN_READ,
        Permission.VULN_READ,
        Permission.REMEDIATION_CREATE,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_READ,
    },
    
    Role.VIEWER: {
        Permission.SCAN_READ,
        Permission.VULN_READ,
        Permission.WORKFLOW_READ,
    },
}


class RBACMiddleware:
    """Role-Based Access Control middleware."""
    
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for a user based on their roles."""
        
        permissions: Set[Permission] = set()
        
        for role_name in user.roles:
            try:
                role = Role(role_name)
                permissions.update(self.role_permissions.get(role, set()))
            except ValueError:
                # Unknown role, skip
                pass
        
        return permissions
    
    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        
        user_permissions = self.get_user_permissions(user)
        return permission in user_permissions
    
    def has_any_permission(self, user: User, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        
        user_permissions = self.get_user_permissions(user)
        return bool(user_permissions.intersection(permissions))
    
    def has_all_permissions(self, user: User, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions."""
        
        user_permissions = self.get_user_permissions(user)
        return all(p in user_permissions for p in permissions)
    
    def has_role(self, user: User, role: Role) -> bool:
        """Check if user has a specific role."""
        
        return role.value in user.roles
    
    def has_any_role(self, user: User, roles: List[Role]) -> bool:
        """Check if user has any of the specified roles."""
        
        return any(role.value in user.roles for role in roles)


# Global RBAC instance
rbac = RBACMiddleware()


def require_role(*roles: Role):
    """Decorator to require specific roles."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user: Optional[User] = kwargs.get("current_user")
            
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            if not rbac.has_any_role(user, list(roles)):
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires one of roles: {[r.value for r in roles]}",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_permission(*permissions: Permission):
    """Decorator to require specific permissions."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user: Optional[User] = kwargs.get("current_user")
            
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            if not rbac.has_any_permission(user, list(permissions)):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required permissions",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
