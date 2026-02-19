"""Data models for Auto-Remediation Agent."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FixType(str, Enum):
    """Types of fixes that can be applied."""
    DEPENDENCY_UPDATE = "dependency_update"
    CONFIG_CHANGE = "config_change"
    CODE_PATCH = "code_patch"
    SECRET_ROTATION = "secret_rotation"
    DOCKERFILE_FIX = "dockerfile_fix"
    IAC_FIX = "iac_fix"
    MANUAL_REQUIRED = "manual_required"


class FixStatus(str, Enum):
    """Status of a fix attempt."""
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    FAILED = "failed"
    REJECTED = "rejected"


class FixConfidence(str, Enum):
    """Confidence level in the fix."""
    HIGH = "high"      # Template-based, well-tested
    MEDIUM = "medium"  # AI-generated with high certainty
    LOW = "low"        # AI-generated, needs review


class FileChange(BaseModel):
    """A single file change in a fix."""
    
    file_path: str
    action: str = Field(..., description="create, modify, delete")
    original_content: Optional[str] = None
    new_content: Optional[str] = None
    diff: Optional[str] = None


class FixTemplate(BaseModel):
    """Template for a common fix pattern."""
    
    id: str
    name: str
    description: str
    fix_type: FixType
    applicable_to: List[str] = Field(default_factory=list, description="CVE patterns, vulnerability types")
    template: str
    variables: List[str] = Field(default_factory=list)
    confidence: FixConfidence = FixConfidence.HIGH


class GeneratedFix(BaseModel):
    """A generated fix for a vulnerability."""
    
    fix_id: str
    vulnerability_id: str
    cve_id: Optional[str] = None
    fix_type: FixType
    
    # Fix details
    title: str
    description: str
    changes: List[FileChange] = Field(default_factory=list)
    
    # Metadata
    confidence: FixConfidence
    template_used: Optional[str] = None
    ai_generated: bool = False
    
    # Verification
    test_commands: List[str] = Field(default_factory=list)
    rollback_steps: List[str] = Field(default_factory=list)
    
    # Status
    status: FixStatus = FixStatus.PENDING
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PullRequestInfo(BaseModel):
    """Information about a created PR."""
    
    pr_number: int
    pr_url: str
    branch_name: str
    title: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    merged_at: Optional[datetime] = None


class RemediationRequest(BaseModel):
    """Request to remediate a vulnerability."""
    
    vulnerability: Dict[str, Any]
    repository: str
    branch: str = "main"
    priority: str = "P2"
    auto_create_pr: bool = True
    require_approval: bool = True


class RemediationResponse(BaseModel):
    """Response with remediation result."""
    
    remediation_id: str
    vulnerability_id: str
    status: FixStatus
    fix: Optional[GeneratedFix] = None
    pr_info: Optional[PullRequestInfo] = None
    message: str
