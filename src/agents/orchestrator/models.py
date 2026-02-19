"""Data models for Orchestrator Agent."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Status of a workflow."""
    PENDING = "pending"
    SCANNING = "scanning"
    ASSESSING = "assessing"
    AWAITING_APPROVAL = "awaiting_approval"
    REMEDIATING = "remediating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowAction(str, Enum):
    """Actions that can be taken in a workflow."""
    SCAN = "scan"
    ASSESS = "assess"
    AUTO_REMEDIATE = "auto_remediate"
    REQUEST_APPROVAL = "request_approval"
    NOTIFY = "notify"
    COMPLETE = "complete"


class AgentStatus(str, Enum):
    """Status of an agent."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AgentInfo(BaseModel):
    """Information about an agent."""
    name: str
    url: str
    status: AgentStatus = AgentStatus.UNKNOWN
    last_check: Optional[datetime] = None
    version: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)


class WorkflowStep(BaseModel):
    """A step in a workflow."""
    step_id: str
    action: WorkflowAction
    status: WorkflowStatus = WorkflowStatus.PENDING
    agent: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Workflow(BaseModel):
    """A complete workflow orchestration."""
    
    workflow_id: str
    repository: str
    branch: str = "main"
    
    # Status
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    
    # Steps
    steps: List[WorkflowStep] = Field(default_factory=list)
    
    # Results
    scan_id: Optional[str] = None
    assessment_id: Optional[str] = None
    remediation_ids: List[str] = Field(default_factory=list)
    
    # Vulnerability counts
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    
    # Decisions
    auto_remediated: int = 0
    awaiting_approval: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Metadata
    triggered_by: str = "manual"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Request to start a workflow."""
    repository: str
    branch: str = "main"
    scan_types: List[str] = Field(
        default=["dependency", "code", "secret", "container", "iac"]
    )
    auto_remediate: bool = True
    notify: bool = True


class WorkflowResponse(BaseModel):
    """Response with workflow status."""
    workflow_id: str
    status: WorkflowStatus
    message: str
    workflow: Optional[Workflow] = None


class ApprovalRequest(BaseModel):
    """Request to approve remediation."""
    workflow_id: str
    vulnerability_ids: List[str]
    approved: bool
    approver: str
    comment: Optional[str] = None
