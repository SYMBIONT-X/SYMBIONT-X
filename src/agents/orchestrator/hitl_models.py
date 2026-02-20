"""Human-in-the-Loop models for SYMBIONT-X."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalType(str, Enum):
    """Type of approval required."""
    REMEDIATION = "remediation"
    DEPLOYMENT = "deployment"
    EXCEPTION = "exception"
    ESCALATION = "escalation"


class AuditAction(str, Enum):
    """Actions that can be audited."""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    ASSESSMENT_COMPLETED = "assessment_completed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    REMEDIATION_STARTED = "remediation_started"
    REMEDIATION_COMPLETED = "remediation_completed"
    REMEDIATION_FAILED = "remediation_failed"
    COMMENT_ADDED = "comment_added"
    EXCEPTION_GRANTED = "exception_granted"
    WORKFLOW_COMPLETED = "workflow_completed"


class Comment(BaseModel):
    """A comment on a vulnerability or workflow."""
    
    comment_id: str
    target_type: str  # vulnerability, workflow, approval
    target_id: str
    author: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None
    mentions: List[str] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    """Request for human approval."""
    
    approval_id: str
    workflow_id: str
    approval_type: ApprovalType
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # What needs approval
    title: str
    description: str
    vulnerability_ids: List[str] = Field(default_factory=list)
    
    # Risk context
    priority: str = "P2"
    risk_summary: str = ""
    recommended_action: str = ""
    
    # Approval details
    requested_by: str = "system"
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Resolution
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None
    
    # Notifications
    notified_users: List[str] = Field(default_factory=list)
    notification_sent_at: Optional[datetime] = None


class AuditLogEntry(BaseModel):
    """An entry in the audit log."""
    
    entry_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: AuditAction
    actor: str  # user or system
    
    # Context
    workflow_id: Optional[str] = None
    vulnerability_id: Optional[str] = None
    approval_id: Optional[str] = None
    
    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class NotificationConfig(BaseModel):
    """Configuration for notifications."""
    
    enabled: bool = True
    
    # Teams webhook
    teams_webhook_url: Optional[str] = None
    
    # Email settings
    email_enabled: bool = False
    email_recipients: List[str] = Field(default_factory=list)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Notification preferences
    notify_on_p0: bool = True
    notify_on_p1: bool = True
    notify_on_approval_required: bool = True
    notify_on_remediation_complete: bool = False
