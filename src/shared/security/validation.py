"""Input validation for SYMBIONT-X."""

import re
from typing import Optional, List, Any, Dict
from functools import wraps

from fastapi import HTTPException
from pydantic import BaseModel, validator, Field


# Validation patterns
PATTERNS = {
    "repository": r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$",
    "branch": r"^[a-zA-Z0-9_./\-]+$",
    "cve_id": r"^CVE-\d{4}-\d{4,}$",
    "package_name": r"^[a-zA-Z0-9_.\-@/]+$",
    "version": r"^[a-zA-Z0-9_.\-+]+$",
    "uuid": r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
    "email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
}

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    r"<script[\s\S]*?>[\s\S]*?</script>",  # XSS
    r"javascript:",  # JS injection
    r"on\w+\s*=",  # Event handlers
    r"eval\s*\(",  # Eval
    r"exec\s*\(",  # Exec
    r"__import__",  # Python import
    r"subprocess",  # Subprocess
    r"os\.system",  # OS command
    r"\$\{.*\}",  # Template injection
    r"\{\{.*\}\}",  # Template injection
]

# Maximum lengths
MAX_LENGTHS = {
    "repository": 200,
    "branch": 100,
    "title": 500,
    "description": 5000,
    "comment": 2000,
    "file_path": 500,
    "package_name": 200,
}


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_pattern(value: str, pattern_name: str) -> bool:
        """Validate value against named pattern."""
        
        pattern = PATTERNS.get(pattern_name)
        if not pattern:
            return True
        
        return bool(re.match(pattern, value))
    
    @staticmethod
    def check_dangerous_content(value: str) -> Optional[str]:
        """Check for dangerous content, return matched pattern if found."""
        
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return pattern
        
        return None
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input."""
        
        # Strip whitespace
        value = value.strip()
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def validate_repository(repo: str) -> str:
        """Validate repository name format."""
        
        repo = InputValidator.sanitize_string(repo, MAX_LENGTHS["repository"])
        
        if not InputValidator.validate_pattern(repo, "repository"):
            raise ValueError(f"Invalid repository format: {repo}")
        
        return repo
    
    @staticmethod
    def validate_branch(branch: str) -> str:
        """Validate branch name format."""
        
        branch = InputValidator.sanitize_string(branch, MAX_LENGTHS["branch"])
        
        if not InputValidator.validate_pattern(branch, "branch"):
            raise ValueError(f"Invalid branch format: {branch}")
        
        return branch
    
    @staticmethod
    def validate_cve_id(cve_id: str) -> str:
        """Validate CVE ID format."""
        
        cve_id = cve_id.upper().strip()
        
        if not InputValidator.validate_pattern(cve_id, "cve_id"):
            raise ValueError(f"Invalid CVE ID format: {cve_id}")
        
        return cve_id
    
    @staticmethod
    def validate_text_input(
        value: str,
        field_name: str,
        required: bool = True,
        max_length: Optional[int] = None,
    ) -> str:
        """Validate general text input."""
        
        if not max_length:
            max_length = MAX_LENGTHS.get(field_name, 1000)
        
        value = InputValidator.sanitize_string(value, max_length)
        
        if required and not value:
            raise ValueError(f"{field_name} is required")
        
        dangerous = InputValidator.check_dangerous_content(value)
        if dangerous:
            raise ValueError(f"Potentially dangerous content detected in {field_name}")
        
        return value


# Validator instance
validator_instance = InputValidator()


def validate_input(func):
    """Decorator to validate input parameters."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Validate string parameters
            for key, value in kwargs.items():
                if isinstance(value, str):
                    dangerous = InputValidator.check_dangerous_content(value)
                    if dangerous:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid input in {key}: potentially dangerous content",
                        )
            
            return await func(*args, **kwargs)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return wrapper


# Pydantic models with validation
class ValidatedScanRequest(BaseModel):
    """Validated scan request."""
    
    repository: str = Field(..., max_length=200)
    branch: str = Field(default="main", max_length=100)
    scan_types: List[str] = Field(default=["dependency", "code", "secret"])
    
    @validator("repository")
    def validate_repo(cls, v):
        return InputValidator.validate_repository(v)
    
    @validator("branch")
    def validate_branch(cls, v):
        return InputValidator.validate_branch(v)
    
    @validator("scan_types")
    def validate_scan_types(cls, v):
        allowed = {"dependency", "code", "secret", "container", "iac"}
        for t in v:
            if t not in allowed:
                raise ValueError(f"Invalid scan type: {t}")
        return v


class ValidatedComment(BaseModel):
    """Validated comment input."""
    
    content: str = Field(..., max_length=2000)
    author: str = Field(..., max_length=100)
    
    @validator("content")
    def validate_content(cls, v):
        return InputValidator.validate_text_input(v, "content")
    
    @validator("author")
    def validate_author(cls, v):
        return InputValidator.validate_text_input(v, "author", max_length=100)
