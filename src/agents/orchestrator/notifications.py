"""Notification system for SYMBIONT-X HITL workflow."""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from hitl_models import ApprovalRequest, NotificationConfig


logger = get_logger("notifications")


class NotificationService:
    """Sends notifications for HITL workflow events."""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self._load_env_config()
    
    def _load_env_config(self):
        """Load configuration from environment variables."""
        
        teams_url = os.getenv("TEAMS_WEBHOOK_URL")
        if teams_url:
            self.config.teams_webhook_url = teams_url
        
        email_recipients = os.getenv("NOTIFICATION_EMAILS")
        if email_recipients:
            self.config.email_recipients = email_recipients.split(",")
            self.config.email_enabled = True
    
    async def send_approval_request(
        self,
        approval: ApprovalRequest,
        dashboard_url: str = "http://localhost:5173/approvals",
    ) -> bool:
        """Send notification for a new approval request."""
        
        if not self.config.enabled:
            logger.debug("Notifications disabled")
            return False
        
        success = True
        
        # Send Teams notification
        if self.config.teams_webhook_url:
            teams_success = await self._send_teams_notification(
                approval, dashboard_url
            )
            success = success and teams_success
        
        # Send email notification
        if self.config.email_enabled and self.config.email_recipients:
            email_success = await self._send_email_notification(
                approval, dashboard_url
            )
            success = success and email_success
        
        return success
    
    async def _send_teams_notification(
        self,
        approval: ApprovalRequest,
        dashboard_url: str,
    ) -> bool:
        """Send Microsoft Teams notification via webhook."""
        
        if not self.config.teams_webhook_url:
            return False
        
        # Build adaptive card for Teams
        card = self._build_teams_card(approval, dashboard_url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.teams_webhook_url,
                    json=card,
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    logger.info(
                        "Teams notification sent",
                        approval_id=approval.approval_id,
                    )
                    return True
                else:
                    logger.warning(
                        "Teams notification failed",
                        status=response.status_code,
                    )
                    return False
                    
        except Exception as e:
            logger.error("Teams notification error", error=str(e))
            return False
    
    def _build_teams_card(
        self,
        approval: ApprovalRequest,
        dashboard_url: str,
    ) -> Dict[str, Any]:
        """Build Microsoft Teams adaptive card."""
        
        priority_colors = {
            "P0": "attention",
            "P1": "attention",
            "P2": "warning",
            "P3": "good",
            "P4": "good",
        }
        
        color = priority_colors.get(approval.priority, "default")
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "dc2626" if approval.priority in ["P0", "P1"] else "ca8a04",
            "summary": f"Approval Required: {approval.title}",
            "sections": [
                {
                    "activityTitle": f"🔔 Approval Required: {approval.title}",
                    "activitySubtitle": f"Priority: {approval.priority} | Type: {approval.approval_type.value}",
                    "facts": [
                        {"name": "Workflow", "value": approval.workflow_id[:8]},
                        {"name": "Vulnerabilities", "value": str(len(approval.vulnerability_ids))},
                        {"name": "Requested By", "value": approval.requested_by},
                        {"name": "Time", "value": approval.requested_at.strftime("%Y-%m-%d %H:%M UTC")},
                    ],
                    "text": approval.description,
                    "markdown": True,
                },
                {
                    "activityTitle": "Risk Summary",
                    "text": approval.risk_summary or "No additional risk information available.",
                },
                {
                    "activityTitle": "Recommended Action",
                    "text": approval.recommended_action or "Please review and approve/reject.",
                },
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Review in Dashboard",
                    "targets": [{"os": "default", "uri": dashboard_url}],
                },
            ],
        }
    
    async def _send_email_notification(
        self,
        approval: ApprovalRequest,
        dashboard_url: str,
    ) -> bool:
        """Send email notification."""
        
        # For now, just log - in production, would use SMTP
        logger.info(
            "Email notification would be sent",
            recipients=self.config.email_recipients,
            approval_id=approval.approval_id,
        )
        return True
    
    async def send_critical_vulnerability_alert(
        self,
        vulnerability_id: str,
        title: str,
        severity: str,
        priority: str,
        repository: str,
    ) -> bool:
        """Send alert for critical vulnerability detected."""
        
        if not self.config.enabled:
            return False
        
        if priority == "P0" and not self.config.notify_on_p0:
            return False
        
        if priority == "P1" and not self.config.notify_on_p1:
            return False
        
        if self.config.teams_webhook_url:
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "dc2626",
                "summary": f"🚨 Critical Vulnerability: {title}",
                "sections": [
                    {
                        "activityTitle": f"🚨 Critical Vulnerability Detected",
                        "facts": [
                            {"name": "ID", "value": vulnerability_id},
                            {"name": "Title", "value": title},
                            {"name": "Severity", "value": severity},
                            {"name": "Priority", "value": priority},
                            {"name": "Repository", "value": repository},
                        ],
                        "markdown": True,
                    },
                ],
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.config.teams_webhook_url,
                        json=card,
                        timeout=10.0,
                    )
                    return response.status_code == 200
            except Exception as e:
                logger.error("Alert notification failed", error=str(e))
                return False
        
        return False
    
    async def send_remediation_complete(
        self,
        workflow_id: str,
        total_fixed: int,
        total_vulnerabilities: int,
    ) -> bool:
        """Send notification when remediation completes."""
        
        if not self.config.notify_on_remediation_complete:
            return False
        
        if self.config.teams_webhook_url:
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "16a34a",
                "summary": "✅ Remediation Complete",
                "sections": [
                    {
                        "activityTitle": "✅ Remediation Complete",
                        "facts": [
                            {"name": "Workflow", "value": workflow_id[:8]},
                            {"name": "Fixed", "value": str(total_fixed)},
                            {"name": "Total", "value": str(total_vulnerabilities)},
                            {"name": "Success Rate", "value": f"{(total_fixed/total_vulnerabilities*100):.1f}%"},
                        ],
                    },
                ],
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.config.teams_webhook_url,
                        json=card,
                        timeout=10.0,
                    )
                    return response.status_code == 200
            except Exception:
                return False
        
        return False


# Global notification service
notification_service = NotificationService()
