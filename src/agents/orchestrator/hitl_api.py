"""Human-in-the-Loop API endpoints for SYMBIONT-X."""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from hitl_models import (
    ApprovalRequest,
    ApprovalStatus,
    ApprovalType,
    AuditAction,
    Comment,
)
from audit_log import audit_log
from notifications import notification_service


logger = get_logger("hitl-api")

router = APIRouter(prefix="/hitl", tags=["human-in-the-loop"])


# ===== In-memory storage =====

approvals_store: dict[str, ApprovalRequest] = {}


# ===== Request/Response Models =====

class CreateApprovalRequest(BaseModel):
    workflow_id: str
    title: str
    description: str
    vulnerability_ids: List[str] = Field(default_factory=list)
    priority: str = "P2"
    risk_summary: str = ""
    recommended_action: str = ""
    requested_by: str = "system"
    expires_in_hours: int = 24


class ApprovalDecision(BaseModel):
    approved: bool
    resolver: str
    comment: Optional[str] = None


class AddCommentRequest(BaseModel):
    target_type: str  # vulnerability, workflow, approval
    target_id: str
    author: str
    content: str
    mentions: List[str] = Field(default_factory=list)


class EditCommentRequest(BaseModel):
    new_content: str
    editor: str


# ===== Approval Endpoints =====

@router.post("/approvals", response_model=dict)
async def create_approval(request: CreateApprovalRequest):
    """Create a new approval request."""
    
    approval_id = str(uuid.uuid4())
    
    approval = ApprovalRequest(
        approval_id=approval_id,
        workflow_id=request.workflow_id,
        approval_type=ApprovalType.REMEDIATION,
        title=request.title,
        description=request.description,
        vulnerability_ids=request.vulnerability_ids,
        priority=request.priority,
        risk_summary=request.risk_summary,
        recommended_action=request.recommended_action,
        requested_by=request.requested_by,
        expires_at=datetime.utcnow() + timedelta(hours=request.expires_in_hours),
    )
    
    approvals_store[approval_id] = approval
    
    # Log to audit
    audit_log.log_approval_requested(
        workflow_id=request.workflow_id,
        approval_id=approval_id,
        priority=request.priority,
        vulnerability_count=len(request.vulnerability_ids),
    )
    
    # Send notification
    await notification_service.send_approval_request(approval)
    
    logger.info(
        "Approval request created",
        approval_id=approval_id,
        workflow_id=request.workflow_id,
    )
    
    return {
        "approval_id": approval_id,
        "status": "pending",
        "message": "Approval request created and notifications sent",
    }


@router.get("/approvals")
async def list_approvals(
    status: Optional[ApprovalStatus] = None,
    workflow_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    """List approval requests with optional filters."""
    
    approvals = list(approvals_store.values())
    
    if status:
        approvals = [a for a in approvals if a.status == status]
    
    if workflow_id:
        approvals = [a for a in approvals if a.workflow_id == workflow_id]
    
    if priority:
        approvals = [a for a in approvals if a.priority == priority]
    
    # Sort by requested_at descending
    approvals = sorted(approvals, key=lambda a: a.requested_at, reverse=True)
    
    return {
        "total": len(approvals),
        "approvals": [a.model_dump() for a in approvals[:limit]],
    }


@router.get("/approvals/pending")
async def get_pending_approvals():
    """Get all pending approval requests."""
    
    pending = [
        a for a in approvals_store.values()
        if a.status == ApprovalStatus.PENDING
    ]
    
    # Check for expired approvals
    now = datetime.utcnow()
    for approval in pending:
        if approval.expires_at and approval.expires_at < now:
            approval.status = ApprovalStatus.EXPIRED
    
    pending = [a for a in pending if a.status == ApprovalStatus.PENDING]
    pending = sorted(pending, key=lambda a: a.requested_at, reverse=True)
    
    return {
        "total": len(pending),
        "approvals": [a.model_dump() for a in pending],
    }


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str):
    """Get a specific approval request."""
    
    if approval_id not in approvals_store:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = approvals_store[approval_id]
    comments = audit_log.get_comments(approval_id)
    
    return {
        "approval": approval.model_dump(),
        "comments": [c.model_dump() for c in comments],
    }


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(approval_id: str, decision: ApprovalDecision):
    """Approve or reject an approval request."""
    
    if approval_id not in approvals_store:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = approvals_store[approval_id]
    
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Approval already {approval.status.value}",
        )
    
    # Update approval
    approval.status = ApprovalStatus.APPROVED if decision.approved else ApprovalStatus.REJECTED
    approval.resolved_by = decision.resolver
    approval.resolved_at = datetime.utcnow()
    approval.resolution_comment = decision.comment
    
    # Log to audit
    audit_log.log_approval_decision(
        approval_id=approval_id,
        workflow_id=approval.workflow_id,
        approved=decision.approved,
        actor=decision.resolver,
        comment=decision.comment,
    )
    
    logger.info(
        "Approval decision made",
        approval_id=approval_id,
        approved=decision.approved,
        resolver=decision.resolver,
    )
    
    return {
        "approval_id": approval_id,
        "status": approval.status.value,
        "message": f"Approval {'approved' if decision.approved else 'rejected'} by {decision.resolver}",
    }


# ===== Comment Endpoints =====

@router.post("/comments")
async def add_comment(request: AddCommentRequest):
    """Add a comment to a vulnerability, workflow, or approval."""
    
    comment = audit_log.add_comment(
        target_type=request.target_type,
        target_id=request.target_id,
        author=request.author,
        content=request.content,
        mentions=request.mentions,
    )
    
    return {
        "comment_id": comment.comment_id,
        "message": "Comment added",
        "comment": comment.model_dump(),
    }


@router.get("/comments/{target_id}")
async def get_comments(target_id: str):
    """Get comments for a specific target."""
    
    comments = audit_log.get_comments(target_id)
    
    return {
        "total": len(comments),
        "comments": [c.model_dump() for c in comments],
    }


@router.put("/comments/{comment_id}")
async def edit_comment(comment_id: str, request: EditCommentRequest):
    """Edit an existing comment."""
    
    comment = audit_log.edit_comment(
        comment_id=comment_id,
        new_content=request.new_content,
        editor=request.editor,
    )
    
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found or not authorized to edit",
        )
    
    return {
        "message": "Comment updated",
        "comment": comment.model_dump(),
    }


# ===== Audit Log Endpoints =====

@router.get("/audit")
async def get_audit_log(
    workflow_id: Optional[str] = None,
    vulnerability_id: Optional[str] = None,
    action: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = Query(100, le=1000),
):
    """Query audit log entries."""
    
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass
    
    entries = audit_log.get_entries(
        workflow_id=workflow_id,
        vulnerability_id=vulnerability_id,
        action=action_enum,
        actor=actor,
        limit=limit,
    )
    
    return {
        "total": len(entries),
        "entries": [e.model_dump() for e in entries],
    }


@router.get("/audit/workflow/{workflow_id}/timeline")
async def get_workflow_timeline(workflow_id: str):
    """Get complete timeline for a workflow."""
    
    entries = audit_log.get_workflow_timeline(workflow_id)
    comments = audit_log.get_comments(workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "timeline": [e.model_dump() for e in entries],
        "comments": [c.model_dump() for c in comments],
    }


@router.get("/audit/export")
async def export_audit_log(
    workflow_id: Optional[str] = None,
    format: str = Query("json", regex="^(json|csv)$"),
):
    """Export audit log entries."""
    
    content = audit_log.export_entries(workflow_id=workflow_id, format=format)
    
    return {
        "format": format,
        "content": content,
    }


@router.get("/audit/stats")
async def get_audit_stats():
    """Get audit log statistics."""
    
    return audit_log.get_stats()
