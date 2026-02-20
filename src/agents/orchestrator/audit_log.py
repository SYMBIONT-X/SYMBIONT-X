"""Audit logging service for SYMBIONT-X."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from hitl_models import AuditLogEntry, AuditAction, Comment


logger = get_logger("audit-log")


class AuditLogService:
    """Service for audit logging all SYMBIONT-X decisions and actions."""
    
    def __init__(self):
        self._entries: List[AuditLogEntry] = []
        self._comments: Dict[str, List[Comment]] = {}  # target_id -> comments
    
    def log(
        self,
        action: AuditAction,
        actor: str,
        workflow_id: Optional[str] = None,
        vulnerability_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an audit entry."""
        
        entry = AuditLogEntry(
            entry_id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            workflow_id=workflow_id,
            vulnerability_id=vulnerability_id,
            approval_id=approval_id,
            details=details or {},
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self._entries.append(entry)
        
        logger.info(
            "Audit log entry",
            action=action.value,
            actor=actor,
            workflow_id=workflow_id,
            success=success,
        )
        
        return entry
    
    def log_scan_started(
        self,
        workflow_id: str,
        repository: str,
        scan_types: List[str],
        actor: str = "system",
    ) -> AuditLogEntry:
        """Log scan started event."""
        
        return self.log(
            action=AuditAction.SCAN_STARTED,
            actor=actor,
            workflow_id=workflow_id,
            details={
                "repository": repository,
                "scan_types": scan_types,
            },
        )
    
    def log_scan_completed(
        self,
        workflow_id: str,
        vulnerabilities_found: int,
        scan_duration_seconds: float,
    ) -> AuditLogEntry:
        """Log scan completed event."""
        
        return self.log(
            action=AuditAction.SCAN_COMPLETED,
            actor="system",
            workflow_id=workflow_id,
            details={
                "vulnerabilities_found": vulnerabilities_found,
                "scan_duration_seconds": scan_duration_seconds,
            },
        )
    
    def log_vulnerability_detected(
        self,
        workflow_id: str,
        vulnerability_id: str,
        severity: str,
        priority: str,
        title: str,
    ) -> AuditLogEntry:
        """Log vulnerability detection."""
        
        return self.log(
            action=AuditAction.VULNERABILITY_DETECTED,
            actor="security-scanner",
            workflow_id=workflow_id,
            vulnerability_id=vulnerability_id,
            details={
                "severity": severity,
                "priority": priority,
                "title": title,
            },
        )
    
    def log_approval_requested(
        self,
        workflow_id: str,
        approval_id: str,
        priority: str,
        vulnerability_count: int,
        actor: str = "orchestrator",
    ) -> AuditLogEntry:
        """Log approval request."""
        
        return self.log(
            action=AuditAction.APPROVAL_REQUESTED,
            actor=actor,
            workflow_id=workflow_id,
            approval_id=approval_id,
            details={
                "priority": priority,
                "vulnerability_count": vulnerability_count,
            },
        )
    
    def log_approval_decision(
        self,
        approval_id: str,
        workflow_id: str,
        approved: bool,
        actor: str,
        comment: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log approval decision."""
        
        return self.log(
            action=AuditAction.APPROVAL_GRANTED if approved else AuditAction.APPROVAL_DENIED,
            actor=actor,
            workflow_id=workflow_id,
            approval_id=approval_id,
            details={
                "decision": "approved" if approved else "rejected",
                "comment": comment,
            },
        )
    
    def log_remediation_started(
        self,
        workflow_id: str,
        vulnerability_ids: List[str],
    ) -> AuditLogEntry:
        """Log remediation started."""
        
        return self.log(
            action=AuditAction.REMEDIATION_STARTED,
            actor="auto-remediation",
            workflow_id=workflow_id,
            details={
                "vulnerability_count": len(vulnerability_ids),
                "vulnerability_ids": vulnerability_ids,
            },
        )
    
    def log_remediation_completed(
        self,
        workflow_id: str,
        vulnerability_id: str,
        fix_type: str,
        success: bool,
        error_message: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log remediation result."""
        
        return self.log(
            action=AuditAction.REMEDIATION_COMPLETED if success else AuditAction.REMEDIATION_FAILED,
            actor="auto-remediation",
            workflow_id=workflow_id,
            vulnerability_id=vulnerability_id,
            details={"fix_type": fix_type},
            success=success,
            error_message=error_message,
        )
    
    # ===== Comments =====
    
    def add_comment(
        self,
        target_type: str,
        target_id: str,
        author: str,
        content: str,
        mentions: Optional[List[str]] = None,
    ) -> Comment:
        """Add a comment to a vulnerability, workflow, or approval."""
        
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            target_type=target_type,
            target_id=target_id,
            author=author,
            content=content,
            mentions=mentions or [],
        )
        
        if target_id not in self._comments:
            self._comments[target_id] = []
        
        self._comments[target_id].append(comment)
        
        # Log the comment action
        self.log(
            action=AuditAction.COMMENT_ADDED,
            actor=author,
            details={
                "target_type": target_type,
                "target_id": target_id,
                "content_preview": content[:100],
            },
        )
        
        return comment
    
    def get_comments(self, target_id: str) -> List[Comment]:
        """Get comments for a target."""
        
        return self._comments.get(target_id, [])
    
    def edit_comment(
        self,
        comment_id: str,
        new_content: str,
        editor: str,
    ) -> Optional[Comment]:
        """Edit an existing comment."""
        
        for comments in self._comments.values():
            for comment in comments:
                if comment.comment_id == comment_id:
                    if comment.author != editor:
                        return None  # Only author can edit
                    
                    comment.content = new_content
                    comment.edited_at = datetime.utcnow()
                    return comment
        
        return None
    
    # ===== Query Methods =====
    
    def get_entries(
        self,
        workflow_id: Optional[str] = None,
        vulnerability_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        actor: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """Query audit log entries."""
        
        entries = self._entries
        
        if workflow_id:
            entries = [e for e in entries if e.workflow_id == workflow_id]
        
        if vulnerability_id:
            entries = [e for e in entries if e.vulnerability_id == vulnerability_id]
        
        if action:
            entries = [e for e in entries if e.action == action]
        
        if actor:
            entries = [e for e in entries if e.actor == actor]
        
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        
        # Sort by timestamp descending
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)
        
        return entries[:limit]
    
    def get_workflow_timeline(self, workflow_id: str) -> List[AuditLogEntry]:
        """Get complete timeline for a workflow."""
        
        entries = [e for e in self._entries if e.workflow_id == workflow_id]
        return sorted(entries, key=lambda e: e.timestamp)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        
        action_counts = {}
        for entry in self._entries:
            action = entry.action.value
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_entries": len(self._entries),
            "total_comments": sum(len(c) for c in self._comments.values()),
            "by_action": action_counts,
        }
    
    def export_entries(
        self,
        workflow_id: Optional[str] = None,
        format: str = "json",
    ) -> str:
        """Export audit log entries."""
        
        entries = self.get_entries(workflow_id=workflow_id, limit=10000)
        
        if format == "json":
            import json
            return json.dumps(
                [e.model_dump() for e in entries],
                default=str,
                indent=2,
            )
        
        # CSV format
        lines = ["timestamp,action,actor,workflow_id,vulnerability_id,success"]
        for e in entries:
            lines.append(
                f"{e.timestamp},{e.action.value},{e.actor},{e.workflow_id or ''},{e.vulnerability_id or ''},{e.success}"
            )
        
        return "\n".join(lines)


# Global audit log service
audit_log = AuditLogService()
