"""SYMBIONT-X Security Module."""

from .auth import AuthMiddleware, get_current_user, require_auth, User
from .rbac import RBACMiddleware, require_role, Role, Permission, require_permission
from .rate_limiter import RateLimiter, rate_limit, default_limiter
from .validation import InputValidator, validate_input, ValidatedScanRequest
from .content_safety import ContentSafetyFilter, filter_ai_content, SafetyLevel
from .middleware import SecurityMiddleware, setup_security

__all__ = [
    # Auth
    "AuthMiddleware",
    "get_current_user",
    "require_auth",
    "User",
    # RBAC
    "RBACMiddleware",
    "require_role",
    "require_permission",
    "Role",
    "Permission",
    # Rate Limiting
    "RateLimiter",
    "rate_limit",
    "default_limiter",
    # Validation
    "InputValidator",
    "validate_input",
    "ValidatedScanRequest",
    # Content Safety
    "ContentSafetyFilter",
    "filter_ai_content",
    "SafetyLevel",
    # Middleware
    "SecurityMiddleware",
    "setup_security",
]
